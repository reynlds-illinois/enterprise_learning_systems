#!/usr/bin/python
#
import sys, csv, os, requests, json, time, datetime, smtplib
#from dateutil.parser import parse
from pprint import pprint
from datetime import date
from email.mime.text import MIMEText
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import getDate
from columnar import columnar
#logScriptStart()
env = getEnv()
canvasToken = env['canvas.token']
canvasUserTokens = env['canvas.user.tokens']
canvasApi = 'https://canvas.illinois.edu/api/v1/'
canvasReportName = "user_access_tokens_csv"
authHeader = {"Authorization": f"Bearer {canvasToken}"}
#canvasObjectsPath = "/var/lib/canvas-mgmt/config/"
#targetFilePath = f'{canvasObjectsPath}canvas_user_token_report.csv'
loopDelay = 10
reportProgress = 0
targetFilePath = canvasUserTokens
#targetFilePath = f'{canvasObjectsPath}{canvasReportName}.csv'
startReportURL = f'{canvasApi}accounts/1/reports/{canvasReportName}'
reportID = requests.post(startReportURL, headers=authHeader).json()['id']
reportURL = f'{canvasApi}accounts/1/reports/{canvasReportName}/{reportID}'
maxRetries = 50
retries = 0
while reportProgress < 100:
    response = requests.get(reportURL, headers=authHeader).json()
    #responseJson = json.loads(response.text)
    reportProgress = int(response['progress'])
    #print(f'=== Progress: {reportProgress}')
    time.sleep(loopDelay)
    retries += 1
    if retries == maxRetries:
        #print('Report generation timed out.')
        exit
if retries < 50:
    with open(targetFilePath, "wb") as file:
        downloadFile = str(response["attachment"]["url"])
        fileLink = requests.get(downloadFile)
        r = file.write(fileLink.content)
    #print(r)