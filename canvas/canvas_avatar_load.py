import os, sys, requests, pprint, datetime, psycopg2, json, ldap3, cx_Oracle, csv, pymssql, base64, zipfile
import PIL
from ldap3 import Server, Connection, ALL, SUBTREE
import time as t
from PIL import Image
from pymssql import *
from requests_toolbelt import sessions
from pprint import pprint
from datetime import *
sys.path.append("/var/lib/canvas-mgmt/bin")    # for canvasFunctions
from canvasFunctions import getEnv
from canvasFunctions import bind2Ldap
#
maxRows = 500000    # Set this for debugging
envDict = getEnv()
env = ''
print()
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (b)eta: ').lower()[0]
    if env == 'p':
        canvasApi = envDict["canvas.api-prod"]
    else:
        canvasApi = envDict["canvas.api-beta"]
print(f'Connected to: {canvasApi}')
print()
canvasToken = input("Enter Canvas token: ")
#
authHeader = {"Authorization": f"Bearer {canvasToken}"}
# credentials load for avatar database, AD, and CD2 DB
icardHost = envDict["icard.host"]
icardUser = envDict["icard.user"]
icardPass = envDict["icard.pass"]
icardDb = envDict["icard.db"]
ldapHost = envDict['UofI.ldap.ad_sys']
ldapBindDn = envDict['UofI.ad_bind']
ldapBindPw = envDict['UofI.ad_bindpwd']
ldapSearchBase = envDict['ad-prod.searchbase_new']
pgHost = envDict['cd2.pg.host']
pgPass = envDict['cd2.pg.pass']
pgUser = envDict['cd2.pg.user']
pgDb = envDict['cd2.pg.db']
pgPort = envDict['cd2.pg.port']
#
today = str(date.today().strftime("%Y-%m-%d"))
timeStart = datetime.now()
#
icardConn = pymssql.connect(server=icardHost, user=icardUser, password=icardPass, database=icardDb)
icardCursor = icardConn.cursor()
#
print('')
avatarSetOnProfile = 0
rowsProcessed = 0
logLocation = f'/var/lib/canvas-mgmt/logs/avatars/avatars_{today}.log'
working_path = '/var/lib/canvas-mgmt/bin/avatars/'
images_path = 'images/'
imagesPath = f'{working_path}images/'
icardSql = """DECLARE @out_value INT;
         EXEC dbo.pshUINPhotoInfo @UINToLookup = %s, @ResultDataFormat = %s, @PhotoNotFoundAction = %s, @ProcedureResultMessage = @out_value OUTPUT;
         SELECT @out_value AS out_value;"""
#
informApiUrl = f'{canvasApi}users/self/files'
mimeType = ('image/jpeg', None)
tempDir = '/var/lib/canvas-mgmt/bin/avatars/tmp/'
valid_mimetypes = ('image/jpeg','image/png','image/gif')
sleepTimer = .5
cd2AvatarsNeeded = f'{working_path}feeder/{today}_avatar_users.csv'
suppressedUsersFile = f'{working_path}feeder/{today}_suppressed_users.csv'
#
def eventLog(eventDetail, logLocation):
    '''save events into a log'''
    logFile = open(logLocation, 'a+')
    logFile.write('%s %s \n' % (t.asctime(), eventDetail))
    logFile.close()
#
def getSuppressedUsers(ldapHost, ldapBindDn, ldapBindPw, ldapSearchBase, logLocation):
    '''Generate a small file of suppressed UINs from Active Directory'''
    ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)
    pageSize = 1000
    cookie = None
    ldapSearchFilter = '(&(objectClass=user)(uiucEduUIN=6*)(uiucEduSuppress=*)(!(uiucEduRegistryInactiveDate=*)))'
    ldapAttributes=['uiucEduUIN', 'sAMAccountName', 'uiucEduSuppress', 'uiucEduRegistryInactiveDate']
    ldapResults = []
    while True:
        ldapConn.search(search_base=ldapSearchBase, search_filter=ldapSearchFilter, attributes=ldapAttributes, search_scope=SUBTREE, paged_size=pageSize, paged_cookie=cookie)
        if ldapConn.entries:
            temp = json.loads(ldapConn.response_to_json())
            for row in temp['entries']:
                ldapResults.append(row['attributes']['uiucEduUIN'])
        cookie = ldapConn.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']
        if not cookie:
            break
    with open(suppressedUsersFile, 'w') as suppressFile:
        suppressFile.write('\n'.join(str(i) for i in ldapResults))
    print(f"|=== Suppressed Accts Acquired: {len(ldapResults)}")
    eventLog(f"|=== Suppressed Accts Acquired: {len(ldapResults)}", logLocation)
    print()
    ldapConn.unbind()
    return ldapResults
#
def getCanvasUsers(cd2AvatarsNeeded, pgHost, pgUser, pgDb, pgPort, logLocation):
    '''Generate a file of Canvas users that have no avatar URL set on their profile'''
    pgConn = psycopg2.connect(host=pgHost,database=pgDb,user=pgUser,password=pgPass)
    pgCursor = pgConn.cursor()
    cd2Query = """select p.integration_id as uin, p.sis_user_id as net_id, u.id as canvas_id
                  from canvas.pseudonyms p
                    join canvas.users u on u.id = p.user_id
                  where u.avatar_image_url is null
                    and p.integration_id like '6%'
                  order by p.integration_id asc"""
    pgCursor.execute(cd2Query)
    cd2Records = pgCursor.fetchall()
    with open(cd2AvatarsNeeded, 'w') as targetUsersFile:
        targetUsersFile.write('\n'.join(str(i) for i in cd2Records))
    print(f'|=== CD2 Avatars Required: {len(cd2Records)}')
    eventLog(f'|=== CD2 Avatars Required: {len(cd2Records)}', logLocation)
    print()
    pgCursor.close()
    pgConn.close()
    return cd2Records
#
def getIcardImage(uin, sleepTimer, icardCursor, icardSql, logLocation):
    '''Acquire and resize the iCard image based on UIN input'''
    imageFileName = f'{uin}.jpg'
    imageFilePath = f'{working_path}{images_path}{uin}.jpg'
    imageFile = open(imageFilePath, 'wb')
    icardParams = (f'{uin}', 'JSON', '0')
    try:
        icardCursor.execute(icardSql, icardParams)
        t.sleep(1)
        data = icardCursor.fetchone()
        dataJson = json.loads(data[0])
    except Exception as e:
        print(f"|=== iCard Image Query Error: {e}")
        eventLog(f"|=== iCard Image Query Error: {e}", logLocation)
        return 0
    if len(dataJson) > 1 and dataJson['ResultDescription'] != 'No image for UIN':
        imgData = base64.standard_b64decode(str(dataJson['ImageJPGBase64']))
        imageFile.write(imgData)
        #
        if os.path.exists(imageFilePath) and os.path.getsize(imageFilePath) > 0:
            imageTemp = Image.open(imageFilePath)
            imResize = imageTemp.resize((300,300), PIL.Image.Resampling.LANCZOS)
            imResize = imResize.convert("RGB")
            imResize.save(imageFilePath)
            print(f'|=== iCard Image acquired: {uin}')
            eventLog(f'|=== iCard Image acquired: {uin}', logLocation)
            imageFile.close()
            imageTemp.close()
            return 1
    else:
        print(f"|=== No Image for {uin}")
        eventLog(f"|=== No Image for {uin}", logLocation)
        return 0
#
def uploadCanvasAvatar(imageFileName, imageFilePath, uin, netID, informApiUrl, authHeader, canvasApi, logLocation):
    '''Upload and set the avatar on the Canvas user profile'''
    uploadInform = {'name': imageFileName,
                    'content_type': mimeType,
                    'size': os.path.getsize(imageFilePath),
                    'parent_folder_path': 'profile pictures',
                    'as_user_id': f'sis_user_id:{netID}'}
    uploadRes = requests.post(informApiUrl,headers=authHeader,data=uploadInform)
    if uploadRes.status_code == 200:
        data = uploadRes.json()
        imageFile = {'file':open(imageFilePath,'rb').read()}
        upload_params = data.get('upload_params')
        upload_url = data.get('upload_url')
        upload_file_res = requests.post(upload_url, data=upload_params, files=imageFile, allow_redirects=False)
        uploadParams = {'as_user_id': f"sis_user_id:{netID}"}
        avatarOptions = requests.get(f"{canvasApi}users/sis_user_id:{netID}/avatars", headers=authHeader, params=uploadParams).json()
        print(f'|=== Image uploaded: {uin} - {netID}')
        eventLog(f'|=== Image uploaded: {uin} - {netID}', logLocation)
        #
        for ao in avatarOptions:
           if ao.get('display_name') == imageFileName:
               token = ao.get('token')
               uploadParams['user[avatar][token]'] = token
               requests.put(f"{canvasApi}users/sis_user_id:{netID}", headers=authHeader, params=uploadParams)
               print(f'|=== Profile image set: {uin} - {netID}')
               eventLog(f'|=== Profile image set: {uin} - {netID}', logLocation)
    else:
        print(f"Canvas User Not Found: {uin} - {netID}")
        eventLog(f"Canvas User Not Found: {uin} - {netID}", logLocation)
# Start the magic
try:
    suppressedAccts = getSuppressedUsers(ldapHost, ldapBindDn, ldapBindPw, ldapSearchBase, logLocation)
    cd2Avatars = getCanvasUsers(cd2AvatarsNeeded, pgHost, pgUser, pgDb, pgPort, logLocation)
except Exception as e:
    print(f'>>> Error: {e}')
#
for row in cd2Avatars:
    rowsProcessed += 1
    if rowsProcessed < maxRows:
        uin = str(row[0])
        netID = str(row[1])
        if uin not in suppressedAccts:
            print(f'>>> STARTING: {uin} - {netID}')
            eventLog(f'>>> STARTING: {uin} - {netID}', logLocation)
            imageFileName = f'{uin}.jpg'
            imageFilePath = f'{working_path}images/{imageFileName}'
            r = getIcardImage(uin, imageFileName, icardCursor, icardSql, logLocation)
            if r == 1:
                uploadCanvasAvatar(imageFileName, imageFilePath, uin, netID, informApiUrl, authHeader, canvasApi, logLocation)
                print(f'### COMPLETE:  {uin} - {netID}')
                eventLog(f'### COMPLETE:  {uin} - {netID}', logLocation)
                avatarSetOnProfile += 1
            print()
        else: continue
#
icardCursor.close()
print()
timeEnd = datetime.now()
tdDiff = timeEnd - timeStart
tdMins = int(round(tdDiff.total_seconds() / 60))
print()
print('|============= STATS ==============')
#print(f'|= Images Needed:         {len(cd2Avatars)}')
print(f'|= Rows processed:        {rowsProcessed}')
#print(f'|= Images Downloaded:     {icardImagesDownloaded}')
#print(f'|= Images Processed:      {icardImagesProcessed}')
#print(f'|= Images uploaded/set:   {avatarUploaded}')
print(f'|= Images Set On Profile: {avatarSetOnProfile}')
print(f'|= Execution time:        {tdMins} minutes')
print('|==================================')
print()
