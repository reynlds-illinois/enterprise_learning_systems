#!/usr/bin/python
#
import sys, csv, requests, datetime
from pprint import pprint
from datetime import date
from email.mime.text import MIMEText
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import getDate
from canvasFunctions import getEnv
from columnar import columnar
#logScriptStart()
realm = realm()
env = getEnv()
canvasToken = realm['canvasToken']
canvasApi = realm['canvasApi']
canvasUserTokensCSV = env['canvas.user.tokens']
authHeader = {"Authorization": f"Bearer {canvasToken}"}
serviceAccts = ['84','94','109','7016','8994','125511','129156','132703','319151','319349','336978','355105','360354','377818','378454','381230','400969','417093','420084','426543']
columnHeader = ['canvas_id', 'canvas_user', 'hint', 'expires', 'last_used']
userTokens = []
loopDelay = 10
dateOnlyFormat = '%Y-%m-%d'
today = str(date.today().strftime('%Y-%m-%d'))
actionChoice = ''
#
def canvasListUserTokens(canvasApi, canvasUserTokensCSV):
    ''' uses the full path of the downloaded all tokens report to genera a list of user-generated tokens '''
    userTokens = []
    with open(canvasUserTokensCSV, 'r') as file:
        allTokens = csv.reader(file)
        for line in allTokens:
            if line[5] == '170000000000016' and line[0] not in serviceAccts:
                canvasUserID = line[0]
                canvasUser = line[1]
                tokenHint = line[2]
                if line[3] == 'never': expiryDate = line[3]
                else:
                    expiryDate = datetime.datetime.fromisoformat(line[3])
                    expiryDate = datetime.datetime.strftime(expiryDate, dateOnlyFormat)
                if line[4] == 'never': lastUsedDate = line[4]
                else:
                    lastUsedDate = datetime.datetime.fromisoformat(line[4])
                    lastUsedDate = datetime.datetime.strftime(lastUsedDate, dateOnlyFormat)
                userTokens.append([canvasUserID, canvasUser, tokenHint, expiryDate, lastUsedDate])
    return userTokens
#
def canvasCreateUserToken(canvasApi, canvasUserID, reason, expiryDate, adminAuth):
    ''' create a user token for someone '''
    createTokenURL = f'{canvasApi}users/{canvasUserID}/tokens'
    params = {'token[purpose]':f'{reason}',
              'token[expires_at]':f'{expiryDate}'}
    try:
        r = requests.post(createTokenURL, params=params, headers=adminAuth)
        return r.json().get('id')
    except Exception as E:
        print(E)
        return False
#
def canvasDeleteUserToken(canvasApi, userTokenInfo, authHeader):
    yesNo = ''
    try:
        canvasUserID = userTokenInfo[0]
        tokenHint = userTokenInfo[2]
        deleteURL = f'{canvasApi}users/{canvasUserID}/tokens/{tokenHint}'
        requests.delete(deleteURL, headers=authHeader)
        print(f'Successfully deleted: {userTokenInfo}')
        print()
    except Exception as E:
        print(E)
#
while actionChoice != 'l' and actionChoice != 'n' and actionChoice != 'd' and actionChoice != 'DE':
    actionChoice = input('Choose an action: (l)ist user tokens, (n)ew user token, (d)elete a user token, (DE)lete all user tokens: ')
    print()
if actionChoice == 'l':
    #canvasAllTokensReportPath = canvasTokensReport(canvasApi, canvasObjectsPath, targetFilePath, canvasReportName, authHeader)
    allUserTokens = canvasListUserTokens(canvasApi, canvasUserTokensCSV)
    print(columnar(allUserTokens, columnHeader, no_borders=True))
    print()
elif actionChoice == 'n':
    yesNo = ''
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
        try:
            r = canvasCreateUserToken(canvasApi, canvasUserID, reason, expiryDate, adminAuth)
            print('Successfully created token.')
            print()
        except Exception as E:
            print('Token NOT successfully created.')
            print(E)
            print()
elif actionChoice == 'DE':
    yesNo1 = ''
    yesNo2 = ''
    userTokens = canvasListUserTokens(canvasApi, canvasUserTokensCSV)
    while yesNo1 != 'y' and yesNo1 != 'n':
        yesNo1 = input('Continue deletion on ALL user-generated tokens (y/n)? ').lower().strip()
        print()
    while yesNo2 != 'y' and yesNo2 != 'n':
        yesNo2 = input('>>> Are you REALLY sure about this? ').lower().strip()
        print()
    if yesNo1 == 'y' and yesNo2 == 'y':
        print('Deleting ALL user-generated tokens...')
        print()
        for userTokenInfo in userTokens:
            canvasDeleteUserToken(canvasApi, userTokenInfo, authHeader)
else:
    tokenChoice = ''
    userTokens = canvasListUserTokens(canvasApi, canvasUserTokensCSV)
    print(columnar(userTokens, columnHeader, no_borders=True))
    while tokenChoice not in [token[2] for token in userTokens]:
        tokenChoice = input('Enter the token HINT to delete: ')
        print()
    for userTokenInfo in userTokens:
        if tokenChoice == userTokenInfo[2]:
            canvasDeleteUserToken(canvasApi, userTokenInfo, authHeader)
            break
    #canvasDeleteUserToken(canvasApi, userTokenInfo, authHeader)
print()
