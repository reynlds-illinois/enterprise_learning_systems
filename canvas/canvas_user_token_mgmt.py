
#!/usr/bin/python
#
import sys, csv, os, requests, urllib, getpass, json, time, datetime, smtplib, pytz
#from dateutil.parser import parse
from pprint import pprint
from datetime import date
from email.mime.text import MIMEText
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import getDate
from columnar import columnar
#logScriptStart()
realm = realm()
canvasToken = realm['canvasToken']
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
canvasReportName = "user_access_tokens_csv"
authHeader = {"Authorization": f"Bearer {canvasToken}"}
canvasObjectsPath = "/var/lib/canvas-mgmt/config/"
targetFilePath = f'{canvasObjectsPath}{canvasReportName}.csv'
serviceAccts = ['84','94','109','8994','125511','129156','132703','319151','319349','336978','355105','377818','378454','381230','400969','417093','420084','426543']
columnHeader = ['canvas_id', 'canvas_user', 'hint', 'expires', 'last_used']
userTokens = []
loopDelay = 10
dateOnlyFormat = '%Y-%m-%d'
today = str(date.today().strftime('%Y-%m-%d'))
actionChoice = False
#
def canvasTokensReport(canvasApi, canvasObjectsPath, targetFilePath, canvasReportName, authHeader):
    ''' Downloads the all tokens report and returns the full path to the CSV file '''
    fileLink = ''
    reportProgress = 0
    targetFilePath = f'{canvasObjectsPath}{canvasReportName}.csv'
    startReportURL = f'{canvasApi}accounts/1/reports/{canvasReportName}'
    reportID = requests.post(startReportURL, headers=authHeader).json()['id']
    reportURL = f'{canvasApi}accounts/1/reports/{canvasReportName}/{reportID}'
    while reportProgress < 100:
        response = requests.get(reportURL, headers=authHeader)
        responseJson = json.loads(response.text)
        reportProgress = int(responseJson['progress'])
        print(f'=== Progress: {reportProgress}')
        time.sleep(loopDelay)
    with open(targetFilePath, "wb") as file:
        downloadFile = str(responseJson["attachment"]["url"])
        fileLink = requests.get(downloadFile)
        file.write(fileLink.content)
    return targetFilePath
#
def canvasListUserTokens(canvasApi, canvasAllTokensReportPath):
    ''' uses the full path of the downloaded all tokens report to genera a list of user-generated tokens '''
    userTokens = []
    with open(canvasAllTokensReportPath, 'r') as file:
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
def canvasCreateUserToken(canvasApi, canvasUserID, reason, expirydate, adminAuth):
    ''' create a user token for someone '''
    createTokenURL = f'{canvasApi}users/{canvasUserID}/tokens'
    params = {'token[purpose]':f'{reason}',
              'token[expires_at]':f'{expiryDate}'}
    try:
        r = requests.post(createTokenURL, params=params, headers=adminAuth)
        return r['id']
    except Exception as E:
        print(E)
        return False
#
def canvasDeleteAllUserTokens(canvasApi, userTokenInfo, adminAuth):
    ''' pass one line at a time from the All User Tokens Report...s/b 5 elements per line '''
    deletedTokens = []
    canvasUserID = userTokenInfo[0]
    canvasUser = userTokenInfo[1]
    tokenHint = userTokenInfo[2]
    expiryDate = userTokenInfo[3]
    lastUsedDate = userTokenInfo[4]
    if expiryDate == 'never': continue
    else:
        expiryDate = datetime.datetime.fromisoformat(userTokenInfo[3])
        expiryDate = datetime.datetime.strftime(expiryDate, dateOnlyFormat)
    if lastUsedDate == 'never': continue
    else:
        lastUsedDate = datetime.datetime.fromisoformat(userTokenInfo[4])
        lastUsedDate = datetime.datetime.strftime(lastUsedDate, dateOnlyFormat)
    while yesNo != 'y' and yesNo != 'n':
        yesNo = input('Continue deletion on this record (y/n)? ').lower().strip()[0]
        print()
    if yesNo == 'n': continue
    else:
        try:
            deleteURL = f'{canvasApi}users/{canvasUserID}/tokens/{tokenHint}'
            requests.delete(deleteURL, headers=adminAuth)
            deletedTokens.append([canvasUserID, canvasUser, tokenHint, expiryDate, lastUsedDate])
            print('Token successfully deleted')
            return True
        except Exception as E:
            print(E)
            return False
    print('==========')
#
while actionChoice != 'l' and actionChoice != 'n' and actionChoice != 'd':
    actionChoice = input('Choose an action: (l)ist user tokens, (n)ew user token, (d)elete all user tokens: ')
    print()
if actionChoice == 'l':
    canvasAllTokensReportPath = canvasTokensReport(canvasApi, canvasObjectsPath, targetFilePath, canvasReportName, authHeader)
    allUserTokens = canvasListUserTokens(canvasApi, canvasAllTokensReportPath)
    print(columnar(allUserTokens, columnHeader, no_borders=True))
    print()
elif actionChoice == 'n':
    netID = input('Enter the NetID of the user that will receive the token:  ')
    print()
    adminToken = getpass.getpass('Enter your SU admin token: ')
    adminAuth = {"Authorization": f"Bearer {adminToken}"}
    canvasUserID = canvasGetUserInfo(netID)[0]
else:
    adminToken = getpass.getpass('Enter your SU admin token: ')
    adminAuth = {"Authorization": f"Bearer {adminToken}"}
    canvasAllTokensReportPath = canvasTokensReport(canvasApi, canvasObjectsPath, targetFilePath, canvasReportName, authHeader)
    userTokens = canvasListUserTokens(canvasApi, canvasAllTokensReportPath)
    for userTokenInfo in userTokens:
        canvasDeleteAllUserTokens(canvasApi, userTokenInfo, adminAuth)
