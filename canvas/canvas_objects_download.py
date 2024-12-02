#!/usr/bin/python
#https://canvas.instructure.com/doc/api/account_reports.html#method.account_reports.available_reports
import sys, os, requests, urllib, json, time, datetime, smtplib
from datetime import date
from email.mime.text import MIMEText
from canvasFunctions import *
objectsList = ["users", "courses", "sections"]
#canvasTerms = ["120228"]        # Optional...can set for active terms only
env = getEnv()
canvasToken = env["canvas.ro-api"]
canvasApi = env["canvas.api-prod"]
canvasReportName = "provisioning_csv"
canvasAccountId = "1"
loopDelay = 20
errors = 0
today = str(date.today().strftime("%Y-%m-%d"))
canvasObjectsPath = str("/my/canvas/config/")     # Target directory for downloaded files
#
for object in objectsList:
    try:
        downloadFilePath = canvasObjectsPath + "/canvas_" + object + ".csv"
        fileLink = ""
        reportProgress = 0
        # start and prep
        canvasEndpoint = f"accounts/{canvasAccountId}/reports/{canvasReportName}"
        reportUrl = urllib.parse.urljoin(canvasApi, canvasEndpoint)
        headers = {"Authorization": f"Bearer {canvasToken}"}
        params = {f"parameters[{object}]":"true"}
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
            time.sleep(loopDelay)
        # extract file url and download file
        with open(downloadFilePath, "wb") as file:
            downloadFile = str(responseJson2["attachment"]["url"])
            fileLink = requests.get(downloadFile, headers=headers)
            file.write(fileLink.content)
    except:
        errors += 1
#
emailFrom = "my_canvas@mydomain.com"
emailRelay = "my_email_relay@mydomain.com"
if errors > 0:
    msg = MIMEText("Canvas Objects Download FAILED")
    msg['From'] = emailFrom
    msg["Subject"] = "Canvas Objects Download FAILED"
    msg['To'] = 'canvas_mgr@mydomain.com'
    emailTo = 'canvas_mgr@mydomain.com'
    S = smtplib.SMTP(emailRelay)
    S.sendmail(emailFrom, emailTo, msg.as_string())
else:
    msg = MIMEText("Canvas Objects Download COMPLETE")
    msg["Subject"] = "Canvas Objects Download COMPLETE"
