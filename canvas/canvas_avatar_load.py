import base64
import json
import os
import sys
import time
from datetime import date, datetime
from io import BytesIO

import psycopg2
import pymssql
import requests
from ldap3 import SUBTREE
from PIL import Image

sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import bind2Ldap

MAX_ROWS = 500000
WORKING_PATH = '/var/lib/canvas-mgmt/bin/avatars/'
LOG_DIRECTORY = '/var/lib/canvas-mgmt/logs/avatars/'
REQUEST_TIMEOUT = 30
ICARD_DELAY_SECONDS = 1
ICARD_SQL = """DECLARE @out_value INT;
         EXEC dbo.pshUINPhotoInfo @UINToLookup = %s, @ResultDataFormat = %s, @PhotoNotFoundAction = %s, @ProcedureResultMessage = @out_value OUTPUT;
         SELECT @out_value AS out_value;"""


def eventLog(eventDetail, logLocation):
    """Append an event to the run log."""
    with open(logLocation, 'a', encoding='utf-8') as log_file:
        log_file.write(f'{time.asctime()} {eventDetail}\n')


def getSuppressedUsers(ldapHost, ldapBindDn, ldapBindPw, ldapSearchBase, suppressedUsersFile, logLocation):
    """Acquire suppressed UINs from Active Directory."""
    ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)
    pageSize = 1000
    cookie = None
    ldapSearchFilter = '(&(objectClass=user)(uiucEduUIN=6*)(uiucEduSuppress=*)(!(uiucEduRegistryInactiveDate=*)))'
    ldapAttributes = ['uiucEduUIN', 'sAMAccountName', 'uiucEduSuppress', 'uiucEduRegistryInactiveDate']
    ldapResults = set()
    try:
        while True:
            ldapConn.search(search_base=ldapSearchBase, search_filter=ldapSearchFilter, attributes=ldapAttributes, search_scope=SUBTREE, paged_size=pageSize, paged_cookie=cookie)
            if ldapConn.entries:
                response = json.loads(ldapConn.response_to_json())
                for row in response['entries']:
                    uins = row['attributes'].get('uiucEduUIN', [])
                    if not isinstance(uins, list):
                        uins = [uins]
                    ldapResults.update(str(uin) for uin in uins)
            controls = ldapConn.result.get('controls', {})
            paging_control = controls.get('1.2.840.113556.1.4.319')
            if paging_control is None:
                raise RuntimeError('LDAP paging response did not include a paging control')
            cookie = paging_control['value']['cookie']
            if not cookie:
                break
        with open(suppressedUsersFile, 'w', encoding='utf-8') as suppressFile:
            suppressFile.write('\n'.join(sorted(ldapResults)))
    finally:
        ldapConn.unbind()
    print(f"|=== Suppressed Accts Acquired: {len(ldapResults)}")
    eventLog(f"|=== Suppressed Accts Acquired: {len(ldapResults)}", logLocation)
    print()
    return ldapResults


def getCanvasUsers(cd2AvatarsNeeded, pgHost, pgUser, pgPass, pgDb, pgPort, logLocation):
    """Get Canvas users without an avatar and write the daily feed file."""
    pgConn = psycopg2.connect(host=pgHost, database=pgDb, user=pgUser, password=pgPass, port=pgPort)
    pgCursor = pgConn.cursor()
    cd2Query = """select p.integration_id as uin, p.sis_user_id as net_id, u.id as canvas_id
                  from canvas.pseudonyms p
                    join canvas.users u on u.id = p.user_id
                  where u.avatar_image_url is null
                    and p.integration_id like '6%'
                  order by p.integration_id asc"""
    try:
        pgCursor.execute(cd2Query)
        cd2Records = pgCursor.fetchall()
        with open(cd2AvatarsNeeded, 'w', encoding='utf-8') as targetUsersFile:
            targetUsersFile.write('\n'.join(str(i) for i in cd2Records))
    finally:
        pgCursor.close()
        pgConn.close()
    print(f'|=== CD2 Avatars Required: {len(cd2Records)}')
    eventLog(f'|=== CD2 Avatars Required: {len(cd2Records)}', logLocation)
    print()
    return cd2Records


def getIcardImage(uin, imageFilePath, icardCursor, icardSql, logLocation):
    """Acquire and resize an iCard image; return whether an image was saved."""
    icardParams = (f'{uin}', 'JSON', '0')
    try:
        icardCursor.execute(icardSql, icardParams)
        time.sleep(ICARD_DELAY_SECONDS)
        data = icardCursor.fetchone()
        if not data or not data[0]:
            raise ValueError('iCard query returned no image data')
        dataJson = json.loads(data[0])
        if dataJson.get('ResultDescription') == 'No image for UIN' or not dataJson.get('ImageJPGBase64'):
            print(f"|=== No Image for {uin}")
            eventLog(f"|=== No Image for {uin}", logLocation)
            return False
        imgData = base64.b64decode(dataJson['ImageJPGBase64'])
        with Image.open(BytesIO(imgData)) as source_image:
            resized_image = source_image.resize((300, 300), Image.Resampling.LANCZOS).convert('RGB')
            resized_image.save(imageFilePath, format='JPEG')
    except Exception as error:
        print(f"|=== iCard Image Error for {uin}: {error}")
        eventLog(f"|=== iCard Image Error for {uin}: {error}", logLocation)
        return False
    print(f'|=== iCard Image acquired: {uin}')
    eventLog(f'|=== iCard Image acquired: {uin}', logLocation)
    return True


def uploadCanvasAvatar(imageFileName, imageFilePath, uin, netID, informApiUrl, authHeader, canvasApi, logLocation):
    """Upload and set a Canvas user's avatar; return whether the profile update succeeded."""
    uploadInform = {'name': imageFileName,
                    'content_type': 'image/jpeg',
                    'size': os.path.getsize(imageFilePath),
                    'parent_folder_path': 'profile pictures',
                    'as_user_id': f'sis_user_id:{netID}'}
    upload_response = requests.post(informApiUrl, headers=authHeader, data=uploadInform, timeout=REQUEST_TIMEOUT)
    upload_response.raise_for_status()
    if not 200 <= upload_response.status_code < 300:
        raise requests.HTTPError(f'Unexpected upload initialization status: {upload_response.status_code}')

    upload_data = upload_response.json()
    upload_params = upload_data.get('upload_params')
    upload_url = upload_data.get('upload_url')
    if not upload_params or not upload_url:
        raise ValueError('Canvas upload initialization response is missing upload parameters')

    with open(imageFilePath, 'rb') as image_file:
        file_response = requests.post(
            upload_url,
            data=upload_params,
            files={'file': image_file},
            allow_redirects=False,
            timeout=REQUEST_TIMEOUT,
        )
    file_response.raise_for_status()

    uploadParams = {'as_user_id': f'sis_user_id:{netID}'}
    avatar_response = requests.get(
        f'{canvasApi}users/sis_user_id:{netID}/avatars',
        headers=authHeader,
        params=uploadParams,
        timeout=REQUEST_TIMEOUT,
    )
    avatar_response.raise_for_status()
    if not 200 <= avatar_response.status_code < 300:
        raise requests.HTTPError(f'Unexpected avatar-list status: {avatar_response.status_code}')

    avatarOptions = avatar_response.json()
    avatar = next(
        (option for option in avatarOptions if option.get('display_name') == imageFileName and option.get('token')),
        None,
    )
    if avatar is None:
        message = f'Uploaded image not available as an avatar: {uin} - {netID}'
        print(message)
        eventLog(message, logLocation)
        return False

    uploadParams['user[avatar][token]'] = avatar['token']
    profile_response = requests.put(
        f'{canvasApi}users/sis_user_id:{netID}',
        headers=authHeader,
        params=uploadParams,
        timeout=REQUEST_TIMEOUT,
    )
    profile_response.raise_for_status()
    if not 200 <= profile_response.status_code < 300:
        raise requests.HTTPError(f'Unexpected profile update status: {profile_response.status_code}')

    print(f'|=== Profile image set: {uin} - {netID}')
    eventLog(f'|=== Profile image set: {uin} - {netID}', logLocation)
    return True


def main():
    envDict = getEnv()
    while True:
        env = input('Please enter the realm to use: (p)rod or (b)eta: ').strip().lower()
        if env in ('p', 'b'):
            break
        print('Please enter p or b.')

    canvasApi = envDict['canvas.api-prod'] if env == 'p' else envDict['canvas.api-beta']
    print(f'Connected to: {canvasApi}')
    canvasToken = input('Enter Canvas token: ').strip()
    if not canvasToken:
        print('A Canvas token is required.')
        return 1
    authHeader = {'Authorization': f'Bearer {canvasToken}'}

    today = date.today().strftime('%Y-%m-%d')
    timeStart = datetime.now()
    logLocation = os.path.join(LOG_DIRECTORY, f'avatars_{today}.log')
    imageDirectory = os.path.join(WORKING_PATH, 'images')
    print()
    print('   |------ TEMP LOCATIONS SET --------')
    print(f'   |    Log Location: {logLocation}')
    print(f'   | Image Directory: {imageDirectory}')
    print('   |----------------------------------')
    print()
    os.makedirs(os.path.dirname(logLocation), exist_ok=True)
    os.makedirs(imageDirectory, exist_ok=True)
    cd2AvatarsNeeded = os.path.join(WORKING_PATH, 'feeder', f'{today}_avatar_users.csv')
    suppressedUsersFile = os.path.join(WORKING_PATH, 'feeder', f'{today}_suppressed_users.csv')

    try:
        suppressedAccts = getSuppressedUsers(
            envDict['UofI.ldap.ad_sys'],
            envDict['UofI.ad_bind'],
            envDict['UofI.ad_bindpwd'],
            envDict['ad-prod.searchbase_new'],
            suppressedUsersFile,
            logLocation,
        )
        cd2Avatars = getCanvasUsers(
            cd2AvatarsNeeded,
            envDict['cd2.pg.host'],
            envDict['cd2.pg.user'],
            envDict['cd2.pg.pass'],
            envDict['cd2.pg.db'],
            envDict['cd2.pg.port'],
            logLocation,
        )
    except Exception as error:
        message = f'>>> Initialization error: {error}'
        print(message)
        eventLog(message, logLocation)
        return 1

    avatarSetOnProfile = 0
    rowsProcessed = 0
    icardConn = None
    icardCursor = None
    try:
        icardConn = pymssql.connect(
            server=envDict['icard.host'],
            user=envDict['icard.user'],
            password=envDict['icard.pass'],
            database=envDict['icard.db'],
        )
        icardCursor = icardConn.cursor()
        for row in cd2Avatars[:MAX_ROWS]:
            rowsProcessed += 1
            uin = str(row[0])
            netID = str(row[1])
            if uin in suppressedAccts:
                continue

            print(f'>>> STARTING: {uin} - {netID}')
            eventLog(f'>>> STARTING: {uin} - {netID}', logLocation)
            imageFileName = f'{uin}.jpg'
            imageFilePath = os.path.join(imageDirectory, imageFileName)
            try:
                if getIcardImage(uin, imageFilePath, icardCursor, ICARD_SQL, logLocation):
                    if uploadCanvasAvatar(
                        imageFileName,
                        imageFilePath,
                        uin,
                        netID,
                        f'{canvasApi}users/self/files',
                        authHeader,
                        canvasApi,
                        logLocation,
                    ):
                        print(f'### COMPLETE: {uin} - {netID}')
                        eventLog(f'### COMPLETE: {uin} - {netID}', logLocation)
                        avatarSetOnProfile += 1
            except Exception as error:
                message = f'>>> Avatar processing error for {uin} - {netID}: {error}'
                print(message)
                eventLog(message, logLocation)
            print()
    except Exception as error:
        message = f'>>> iCard connection error: {error}'
        print(message)
        eventLog(message, logLocation)
        return 1
    finally:
        if icardCursor is not None:
            icardCursor.close()
        if icardConn is not None:
            icardConn.close()

    tdMins = int(round((datetime.now() - timeStart).total_seconds() / 60))
    print('|============= STATS ==============')
    print(f'|= Rows processed:        {rowsProcessed}')
    print(f'|= Images Set On Profile: {avatarSetOnProfile}')
    print(f'|= Execution time:        {tdMins} minutes')
    print('|==================================')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
