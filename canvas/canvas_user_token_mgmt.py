#!/usr/bin/python
#
import sys, csv, requests, time, datetime, smtplib, pytz
from pprint import pprint
from datetime import date
from email.mime.text import MIMEText
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import getDate
from canvasFunctions import getEnv
from canvasFunctions import logScriptStart
from columnar import columnar
logScriptStart()
realm = realm()
env = getEnv()
canvasToken = realm['canvasToken']
canvasApi = realm['canvasApi']
canvasUserTokens = env['canvas.user.tokens']
authHeader = {"Authorization": f"Bearer {canvasToken}"}
serviceAccts = ['84','94','109','8994','125511','129156','132703','319151','319349','336978','355105','377818','378454','381230','400969','417093','420084','426543']
columnHeader = ['canvas_id', 'canvas_user', 'hint', 'expires', 'last_used']
userTokens = []
loopDelay = 10
dateOnlyFormat = '%Y-%m-%d'
today = str(date.today().strftime('%Y-%m-%d'))
actionChoice = ''
#
def canvasListUserTokens(canvasApi, canvasUserTokens):
    ''' uses the full path of the downloaded all tokens report to genera a list of user-generated tokens '''
    userTokens = []
    with open(canvasUserTokens, 'r') as file:
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
def canvasDeleteAllUserTokens(canvasApi, userTokenInfo, authHeader):
    ''' pass one line at a time from the All User Tokens Report...s/b 5 elements per line '''
    #yesNoT = ''
    #deletedTokens = []
    canvasUserID = userTokenInfo[0]
    canvasUser = userTokenInfo[1]
    tokenHint = userTokenInfo[2]
    expiryDate = userTokenInfo[3]
    lastUsedDate = userTokenInfo[4]
    if expiryDate != 'never':
        expiryDate = datetime.datetime.fromisoformat(userTokenInfo[3])
        expiryDate = datetime.datetime.strftime(expiryDate, dateOnlyFormat)
    if lastUsedDate != 'never':
        lastUsedDate = datetime.datetime.fromisoformat(userTokenInfo[4])
        lastUsedDate = datetime.datetime.strftime(lastUsedDate, dateOnlyFormat)
        print()
    try:
        deleteURL = f'{canvasApi}users/{canvasUserID}/tokens/{tokenHint}'
        requests.delete(deleteURL, headers=authHeader)
        print(f'{canvasUser} - Token successfully deleted')
    except Exception as E:
        print(f'{canvasUser} - ERROR = {E}')
    print('==========')
#
def canvasDeleteUserToken(canvasApi, userTokenInfo, authHeader):
    yesNo = ''
    try:
        canvasUserID = userTokenInfo[0]
        tokenHint = userTokenInfo[2]
        while yesNo != 'y' and yesNo != 'n':
            pprint(userTokenInfo)
            print()
            yesNo = input('Continue deletion on this record (y/n)? ').lower().strip()
            print()
        if yesNo == 'y':
            deleteURL = f'{canvasApi}users/{canvasUserID}/tokens/{tokenHint}'
            requests.delete(deleteURL, headers=authHeader)
            print('Token successfully deleted. This will show up in the next run of user-generated tokens report.')
    except Exception as E:
        print(E)
#
while actionChoice != 'l' and actionChoice != 'n' and actionChoice != 'd' and actionChoice != 'DE':
    actionChoice = input('Choose an action: (l)ist user tokens, (n)ew user token, (d)elete a user token, (DE)lete all user tokens: ')
    print()
if actionChoice == 'l':
    allUserTokens = canvasListUserTokens(canvasApi, canvasUserTokens)
    print(columnar(allUserTokens, columnHeader, no_borders=True))
    print()
elif actionChoice == 'n':
    yesNo = ''
    netID = input('Enter the NetID of the user that will receive the token:  ')
    print()
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
    userTokens = canvasListUserTokens(canvasApi, canvasUserTokens)
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
            try:
                canvasDeleteAllUserTokens(canvasApi, userTokenInfo, authHeader)
                pprint(userTokenInfo)
                print()
            except Exception as E:
                print(E)
                print()
            time.sleep(1)
else:
    tokenChoice = ''
    userTokens = canvasListUserTokens(canvasApi, canvasUserTokens)
    print(columnar(userTokens, columnHeader, no_borders=True))
    while tokenChoice not in [token[2] for token in userTokens]:
        tokenChoice = input('Enter the token HINT to delete: ')
        print()
    for userTokenInfo in userTokens:
        if tokenChoice == userTokenInfo[2]:
            canvasDeleteUserToken(canvasApi, userTokenInfo, authHeader)
            break
print()
