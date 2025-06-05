#!/usr/bin/python
#
import os, sys, csv, requests, datetime, time
from pprint import pprint
from datetime import date, timedelta
from datetime import datetime
from email.mime.text import MIMEText
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import getDate
from canvasFunctions import getEnv
from canvasFunctions import logScriptStart
from boxsdk import JWTAuth, Client
from boxsdk.exception import BoxAPIException
from boxsdk.object.collaboration import CollaborationRole
from columnar import columnar
#
logScriptStart()
realm = realm()
env = getEnv()
canvasToken = realm['canvasToken']
canvasApi = realm['canvasApi']
canvasUserTokensCSV = env['canvas.user.tokens']
authHeader = {"Authorization": f"Bearer {canvasToken}"}
serviceAccts = ['84','94','109','7016','8994','125511','129156','132703','319151','319349','336978','355105','360354','377818','378454','381230','400969','417093','420084','426543']
columnHeader = ['canvas_id', 'netid', 'canvas_user', 'hint', 'expires', 'last_used']
userTokens = []
tokenTempFolder = '/var/lib/canvas-mgmt/tmp'
jwtAuthFile = env['uofi.box.jwtauth.file']
boxJwtAuthFile = env['uofi.box.jwtauth.file']
boxAuth = JWTAuth.from_settings_file(boxJwtAuthFile)
boxParentFolderID = env['uofi.box.api.token.folder']
boxClient = Client(boxAuth)
boxRequstorRole = 'Viewer'
canvasUsersFilePath = '/var/lib/canvas-mgmt/config/canvas_users.csv'
loopDelay = 2
dateOnlyFormat = '%Y-%m-%d'
today = str(date.today().strftime('%Y-%m-%d'))
actionChoice = ''
#
def loadCanvasUsers(canvasUsersFilePath):
    """ Loads the canvas_users.csv file into memory as a dictionary """
    canvasUsers = []
    with open(canvasUsersFilePath, 'r') as csvFile:
        reader = csv.reader(csvFile)
        for csvrow in reader:
            canvasUsers.append(csvrow)
    # Remove the header row from the list
    canvasUsers.pop(0)
    return canvasUsers
#
def canvasListUserTokens(canvasUserTokensCSV, canvasAllUsers):
    ''' uses the full path of the downloaded all tokens report to genera a list of user-generated tokens '''
    userTokens = []
    print('  ... Loading list of user-generated tokens ...')
    print()
    with open(canvasUserTokensCSV, 'r') as file:
        allTokens = csv.reader(file)
        for line in allTokens:
            if line[5] == '170000000000016' and line[0] not in serviceAccts:
                canvasUserID = line[0]
                canvasUser = line[1]
                tokenHint = line[2]
                if line[3] == 'never': expiryDate = line[3]
                else:
                    expiryDate = datetime.fromisoformat(line[3])
                    expiryDate = datetime.strftime(expiryDate, dateOnlyFormat)
                if line[4] == 'never': lastUsedDate = line[4]
                else:
                    lastUsedDate = datetime.fromisoformat(line[4])
                    lastUsedDate = datetime.strftime(lastUsedDate, dateOnlyFormat)
                for row in canvasAllUsers:
                    if canvasUserID == row[0]:
                        netID = row[1]
                        break
                userTokens.append([canvasUserID, netID, canvasUser, tokenHint, expiryDate, lastUsedDate])
    userTokens = sorted(userTokens, key=lambda x: x[1])
    return userTokens
#
def canvasCreateUserToken(canvasApi, canvasUserID, reason, expiryDate, adminAuth):
    ''' create a user token for someone '''
    createTokenURL = f'{canvasApi}users/{canvasUserID}/tokens'
    params = {'token[purpose]':f'> {reason}',
              'token[expires_at]':f'{expiryDate}'}
    try:
        r = requests.post(createTokenURL, params=params, headers=adminAuth)
        return r.json()
    except Exception as E:
        print(E)
        return False
#
def canvasDeleteUserToken(canvasApi, canvasUserID, tokenHint, authHeader):
    #yesNo = ''
    try:
        #canvasUserID = userTokenInfo[0]
        #tokenHint = userTokenInfo[2]
        deleteURL = f'{canvasApi}users/{canvasUserID}/tokens/{tokenHint}'
        requests.delete(deleteURL, headers=authHeader)
        print(f'Successfully deleted token {tokenHint} for user {canvasUserID}.')
        print()
    except Exception as E:
        print(E)
#
def uploadToBox(targetFilePath, targetFileName, boxParentFolderID, boxFolderName, requestorEmailAddress):
    try:
        # create target folder in BOX
        boxCreateTargetFolder = boxClient.folder(boxParentFolderID).create_subfolder(boxFolderName)
        boxTargetFolderID = int(boxCreateTargetFolder['id'])
        print('  = Successfully created the BOX target folder.')
        print()
        # upload local CSV file to new BOX target folder
        r = boxClient.folder(boxTargetFolderID).upload(targetFilePath, targetFileName)
        #print(r)
        print('  = Successfully uploaded the CSV to BOX.')
        # share new BOX target folder with TDX requestor
        x = boxClient.folder(boxTargetFolderID).collaborate_with_login(requestorEmailAddress,CollaborationRole.VIEWER)
        boxSharedLink = f'https://uofi.box.com/folder/{boxTargetFolderID}'
        print()
        print('  ==')
        print(f'  == Folder successfully shared in BOX:  {boxSharedLink}')
        print('  ==')
    except Exception as e:
        print(f'!!! Error During BOX Actions: {e}')
#
canvasAllUsers = loadCanvasUsers(canvasUsersFilePath)
#
while actionChoice != 'N30' and actionChoice != 'NN' and actionChoice != 'P' and actionChoice != 'l' and actionChoice != 'n' and actionChoice != 'd' and actionChoice != 'DE':
    print('Choose an action: (l)ist user tokens')
    print('                  (n)ew user token')
    print('                  (d)elete a specific user token')
    print('                  (P)rompted delete of tokens one at a time')
    print('                  (NN) delete tokens without expiry or last used dates')
    print('                  (N30) delete unsued tokens or those used longer than 30 days ago')
    print('                  (DELALL)lete all user tokens without prompt')
    print()
    actionChoice = input('                : ')
    print()
if actionChoice == 'l':
    #canvasAllTokensReportPath = canvasTokensReport(canvasApi, canvasObjectsPath, targetFilePath, canvasReportName, authHeader)
    allUserTokens = canvasListUserTokens(canvasUserTokensCSV, canvasAllUsers)
    print(columnar(allUserTokens, columnHeader, no_borders=True))
    print()
elif actionChoice == 'n':
    yesNo = ''
    tdxTicket = input('Enter the TDX ticket number: ')
    print()
    netID = input('Enter the NetID of the user that will receive the token:  ')
    print()
    #adminToken = getpass.getpass('Enter your SU admin token: ')
    adminToken = canvasToken
    adminAuth = {"Authorization": f"Bearer {adminToken}"}
    canvasUserInfo = canvasGetUserInfo(netID)
    canvasUserID = canvasUserInfo[0]
    displayName = canvasUserInfo[3]
    print()
    reason = input('Enter a short reason for this request: ')
    print()
    expiryDate = getDate()
    print()
    while yesNo != 'y' and yesNo != 'n':
        print('  ===== Summary of Changes =====')
        print(f'  = NetID:       {netID}')
        print(f'  = Reason:      {reason}')
        print(f'  = Expiry Date: {expiryDate}')
        print('  ==============================')
        print()
        yesNo = input('>>> Continue (y/n)? ').lower().split()[0]
        print()
    if yesNo == 'y':
        tokenTempFileName = f'{netID}_TDX-{tdxTicket}_token.txt'
        tokenTempFile = f'{tokenTempFolder}/{tokenTempFileName}'
        requestorEmailAddress = f'{netID}@illinois.edu'
        try:
            newToken = canvasCreateUserToken(canvasApi, canvasUserID, reason, expiryDate, adminAuth)
            print('Successfully created token.')
            print(f'  = NetID:       {netID}')
            print(f'  = Reason:      {reason}')
            print(f'  = Expiry Date: {expiryDate}')
            print(f'    >>>>> Token: {newToken["visible_token"]}')
            print()
        except Exception as E:
            print('Token NOT successfully created.')
            print(E)
            print()
        try:
            with open(tokenTempFile, 'w') as localTempFile:
                localTempFile.write(f'''NetID:  {netID}
Expiration:  {expiryDate}
Token:  {newToken["visible_token"]}
''')
            # upload local CSV file to new BOX target folder
            r = boxClient.folder(boxParentFolderID).upload(tokenTempFile, tokenTempFileName)
            print(r)
            newTokenFileID = r['id']
            print('  = Successfully uploaded the TOKEN_FILE to BOX.')
            # share new BOX target file with TDX requestor
            x = boxClient.file(newTokenFileID).collaborate_with_login(requestorEmailAddress,CollaborationRole.VIEWER)
            boxSharedLink = f'https://uofi.box.com/file/{newTokenFileID}'
            print()
            print('  ==')
            print(f'  == Token File successfully shared in BOX:  {boxSharedLink}')
            print('  ==')
            print()
            # delete local temp file
            os.remove(tokenTempFile)
        except BoxAPIException as e:
            print(f'!!! Error During BOX Actions: {e}')
            print()
        except Exception as e:
            print(f'!!! Error During BOX Actions: {e}')
            print()
    else:
        print('Token NOT created.')
        print()
#
elif actionChoice == 'DELALL':
    yesNo1 = ''
    yesNo2 = ''
    userTokens = canvasListUserTokens(canvasUserTokensCSV, canvasAllUsers)
    print(columnar(userTokens, columnHeader, no_borders=True))
    while yesNo1 != 'y' and yesNo1 != 'n':
        yesNo1 = input('Continue deletion on ALL user-generated tokens (y/n)? ').lower().strip()
        print()
    while yesNo2 != 'y' and yesNo2 != 'n':
        yesNo2 = input('>>> Are you REALLY sure about this (y/n)? ').lower().strip()
        print()
    if yesNo1 == 'y' and yesNo2 == 'y':
        print('Deleting ALL user-generated tokens...')
        print()
        for userTokenInfo in userTokens:
            canvasUserID = userTokenInfo[0]
            tokenHint = userTokenInfo[3]
            canvasDeleteUserToken(canvasApi, canvasUserID, tokenHint, authHeader)
            #time.sleep(loopDelay)
elif actionChoice == 'P':
    userTokens = canvasListUserTokens(canvasUserTokensCSV, canvasAllUsers)
    print(columnar(userTokens, columnHeader, no_borders=True))
    for userTokenInfo in userTokens:
        yesNo = ''
        print(userTokenInfo)
        while yesNo not in ['y', 'n']:
            yesNo = input('  > Delete this token (y/n)? ').lower().strip()
        if yesNo == 'n': continue
        else:
            canvasUserID = userTokenInfo[0]
            tokenHint = userTokenInfo[3]
            canvasDeleteUserToken(canvasApi, canvasUserID, tokenHint, authHeader)
elif actionChoice == 'NN':
    yesNo = ''
    while yesNo != 'y' and yesNo != 'n':
        yesNo = input('Continue deleting all tokens with no expiry or last used date (y/n)? ').lower().strip()
        print()
    if yesNo == 'y':
        userTokens = canvasListUserTokens(canvasUserTokensCSV, canvasAllUsers)
        for userTokenInfo in userTokens:
            if userTokenInfo[4] == 'never' and userTokenInfo[5] == 'never':
                print(userTokenInfo)
                canvasUserID = userTokenInfo[0]
                tokenHint = userTokenInfo[3]
                canvasDeleteUserToken(canvasApi, canvasUserID, tokenHint, authHeader)
            else: continue
elif actionChoice == 'N30':
    yesNo = ''
    while yesNo != 'y' and yesNo != 'n':
        yesNo = input('Continue deleting all unused tokens, or those used greater than 30 days ago (y/n)? ').lower().strip()
        print()
    if yesNo == 'y':
        userTokens = canvasListUserTokens(canvasUserTokensCSV, canvasAllUsers)
        today = datetime.now()
        thirtyDaysAgo = today - timedelta(days=30)
        thirtyDaysAgo = thirtyDaysAgo.strftime('%Y-%m-%d')
        for userTokenInfo in userTokens:
            if userTokenInfo[5] != 'never':  # Ensure lastUsedDate is not 'never'
                lastUsedDate = datetime.strptime(userTokenInfo[5], '%Y-%m-%d')  # Convert to datetime
                if lastUsedDate < datetime.strptime(thirtyDaysAgo, '%Y-%m-%d'):  # Compare dates
                    print(userTokenInfo)
                    canvasUserID = userTokenInfo[0]
                    tokenHint = userTokenInfo[3]
                    canvasDeleteUserToken(canvasApi, canvasUserID, tokenHint, authHeader)
else:
    tokenChoice = ''
    canvasUserID = ''
    userTokens = canvasListUserTokens(canvasUserTokensCSV, canvasAllUsers)
    print(columnar(userTokens, columnHeader, no_borders=True))
    while tokenChoice not in [token[2] for token in userTokens] and canvasUserID not in [token[0] for token in userTokens]:
        canvasUserID = input('Enter the canvas user ID of the token to delete: ')
        print()
        tokenHint = input('Enter the token HINT to delete: ')
        print()
    #for userTokenInfo in userTokens:
    #    if tokenHint == userTokenInfo[2] and canvasUserID == userTokenInfo[0]:
    canvasDeleteUserToken(canvasApi, canvasUserID, tokenHint, authHeader)
    #        break
print()
