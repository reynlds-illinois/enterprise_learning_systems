#!/usr/bin/python
#
import sys, os, requests, urllib, json, time, datetime, tzlocal, pytz
from columnar import columnar
from datetime import date
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
envDict = getEnv()
env = 'x'
#
print('')
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower().strip()
    if env == 'p':
        canvasApi = envDict["canvas.api-prod"]
        canvasToken = envDict["canvas.write-token"]
        envLabel = "PROD"
    else:
        canvasApi = envDict["canvas.api-beta"]
        canvasToken = envDict["canvas.write-token"]
        envLabel = "STAGE"
canvasAccountId = "1"
authHeaders = {"Authorization": f"Bearer {canvasToken}"}
today = str(date.today().strftime("%Y-%m-%d"))
params = {"per_page":25}
logScriptStart()
imports = []
importsTable = []
importIDs = []
importStartedAt = ''
importCreatedAt = ''
importUpdatedAt = ''
cancelID = 'x'
cancelProceed = ''
eXit = 0
timeFormat = "%Y-%m-%d  %H:%M:%S"
sisHeader = ['id', 'started_at', 'progress %', 'workflow_state', 'user', 'csv_filename', 'csv_upload_status']
print('')
#
sisUrl = f"{canvasApi}accounts/1/sis_imports"
r = requests.get(sisUrl, params=params, headers=authHeaders)
imports = json.loads(r.text)
for item in range(0, len(imports['sis_imports'])):
    importID = imports['sis_imports'][item]['id']
    if imports['sis_imports'][item]['started_at']:
        importStartedAt = imports['sis_imports'][item]['started_at'].replace("T"," ").replace("Z","")
    else:
        impotStartedAt = "None"
    if imports['sis_imports'][item]['created_at']:
        importCreatedAt = imports['sis_imports'][item]['created_at'].replace("T"," ").replace("Z","")
    else:
        importCreatedAt = "None"
    if imports['sis_imports'][item]['updated_at']:
        importUpdatedAt = imports['sis_imports'][item]['updated_at'].replace("T"," ").replace("Z","")
    else:
        importUpdatedAt = "None"
    importProgress = imports['sis_imports'][item]['progress']
    workflowState = imports['sis_imports'][item]['workflow_state']
    importUser = imports['sis_imports'][item]['user']['sis_user_id']
    if workflowState == "initializing" or workflowState == "created" or workflowState == "importing" or workflowState == "cleanup_batch" or workflowState == "restoring":
        #importsTable.append([importStartedAt, importProgress, workflowState, importUser])
        importIDs.append(str(importID))
        print(f"ID: {imports['sis_imports'][item]['id']}")
        print(f"    Created At:         {importCreatedAt}")
        print(f"    Started At:         {importStartedAt}")
        print(f"    Updated At:         {importUpdatedAt}")
        print(f"    Progress:           {importProgress}%")
        print(f"    Workflow State:     {workflowState}")
        print(f"    User/Service Name:  {importUser}")
        print('')
if len(importIDs) > 0:
    #print(f"importIDs: {importIDs}", type(importIDs))
    while cancelID != 'q' and cancelID not in importIDs:
        cancelID = input("What import ID would you like to cancel (q/Q to exit without changes): ").lower()
        #print(f"cancelID: {cancelID}")
    if cancelID == 'q':
        print('')
        print('Exiting without changes...')
        print('')
        #break
    else:
        print(f"Canceling import for ID # {cancelID}.")
        sisCancelUrl = f"{canvasApi}sis_imports/{cancelID}/abort"
        r = requests.put(sisCancelUrl, headers=authHeaders)
        time.sleep(2)
        print(r.status_code)
        print('')
        sisIDCheck = f"{canvasApi}sis_imports/{cancelID}"
        r = requests.get(sisIDCheck, headers=authHeaders)
        print(r.status_code, r.text)
        print('')
        #break
else:
    print('')
    print('No imports are currently taking place')
    print('')
