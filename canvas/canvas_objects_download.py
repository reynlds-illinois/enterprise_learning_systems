#!/usr/bin/python

import sys, os, requests, urllib, json, time, datetime, smtplib
from datetime import date
from email.mime.text import MIMEText
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
logScriptStart()
objectsList = ["users", "courses", "sections", "accounts"]
env = getEnv()
canvasToken = env["canvas.ro-token"]
canvasApi = env["canvas.api-prod"]
canvasReportName = "provisioning_csv"
canvasAccountId = "1"
loopDelay = 20
errors = 0
today = str(date.today().strftime("%Y-%m-%d"))
canvasObjectsPath = str("/var/lib/canvas-mgmt/config/")
#
for object in objectsList:
    print(f"> Processing:  {object}")
    print()
    try:
        #emailResults = []
        #emailResults.insert(f"=== {object} download starting")
        ###print(f"=== {now()} {object} download starting")
        #logFilePath = str(canvasObjectsPath + "/var/lib/canvas-mgmt/logs/" + object + "_" + today + ".log")
        downloadFilePath = canvasObjectsPath + "canvas_" + object + ".csv"
        fileLink = ""
        reportProgress = 0
        #
        # start and prep
        canvasEndpoint = f"accounts/{canvasAccountId}/reports/{canvasReportName}"
        reportUrl = urllib.parse.urljoin(canvasApi, canvasEndpoint)
        headers = {"Authorization": f"Bearer {canvasToken}"}
        params = {f"parameters[{object}]":"true"}
        #
        # initiate report through api
        response = requests.post(reportUrl, headers=headers, params=params).json()
        reportId = response["id"]
        reportEndpoint = f"accounts/{canvasAccountId}/reports/{canvasReportName}/{reportId}"
        # check report status and return finalized response in json
        while reportProgress < 100:
            checkReportUrl = urllib.parse.urljoin(canvasApi,reportEndpoint)
            response = requests.get(checkReportUrl, headers=headers)
            responseJson2 = json.loads(response.text)
            reportProgress = int(responseJson2['progress'])
            ###print(f"checking {object} report progress. Currently: {reportProgress}")
            time.sleep(loopDelay)
        #
        # extract file url and download file
        with open(downloadFilePath, "wb") as file:
            downloadFile = str(responseJson2["attachment"]["url"])
            fileLink = requests.get(downloadFile)
            file.write(fileLink.content)
        #emailResults.insert(f"=== {object} download completed")
        ###print(f"=== {now()} {object} download completed")
    except:
        errors += 1
        #emailResults.append(f"!!! FAILED to download {object} file!!!")
        ###print(f"!!! {now()} FAILED to download {object} file !!!")
#
emailFrom = "canvas@illinois.edu"
emailRelay = "express-smtp.cites.illinois.edu"
if errors > 0:
    msg = MIMEText("Canvas Objects Download FAILED")
    msg['From'] = emailFrom
    msg["Subject"] = "Canvas Objects Download FAILED"
    msg['To'] = 'reynlds@illinois.edu'
    emailTo = 'reynlds@illinois.edu'
    S = smtplib.SMTP(emailRelay)
    S.sendmail(emailFrom, emailTo, msg.as_string())
    msg['To'] = 'ashbeal@illinois.edu'
    emailTo = 'ashbeal@illinois.edu'
    S = smtplib.SMTP(emailRelay)
    S.sendmail(emailFrom, emailTo, msg.as_string())
#else:
    #msg = MIMEText("Canvas Objects Download COMPLETE")
    #msg["Subject"] = "Canvas Objects Download COMPLETE"
#for address in range(0, len(emailTo)):
#msg['From'] = emailFrom
#
#msg['To'] = 'reynlds@illinois.edu'
#emailTo = 'reynlds@illinois.edu'
#S = smtplib.SMTP(emailRelay)
#S.sendmail(emailFrom, emailTo, msg.as_string())
#msg['To'] = 'ashbeal@illinois.edu'
#emailTo = 'ashbeal@illinois.edu'
#S = smtplib.SMTP(emailRelay)
#S.sendmail(emailFrom, emailTo, msg.as_string())
