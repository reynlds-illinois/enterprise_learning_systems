###############################################################################
# List most current 10 SIS uploads to Canvas
###############################################################################
#!/usr/bin/python
import sys, os, requests, urllib, json, time, datetime, tzlocal, pytz
from columnar import columnar
from datetime import date
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
from columnar import columnar
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
print('')
print(f"Connected to Canvas {envLabel}: {canvasApi}")
print('')
#
canvasAccountId = "1"
authHeaders = {"Authorization": f"Bearer {canvasToken}"}
today = str(date.today().strftime("%Y-%m-%d"))
params = {"per_page":10}
imports = []
timeFormat = "%Y-%m-%d  %H:%M:%S"
importsHeader = ['ID', 'STATE', 'USER', 'FILE','CREATED', 'STARTED', 'ENDED', 'URL']
print('')
#
sisUrl = f"{canvasApi}accounts/1/sis_imports"
r = requests.get(sisUrl, params=params, headers=authHeaders).json()
for item in r['sis_imports']:
    if item['started_at']:
        importStartedAt = item['started_at'].replace("T"," ").replace("Z","")
    else:
        importStartedAt = "None"
    if item['created_at']:
        importCreatedAt = item['created_at'].replace("T"," ").replace("Z","")
    else:
        importCreatedAt = "None"
    if item['ended_at']:
        importEndedAt = item['ended_at'].replace("T"," ").replace("Z","")
    else:
        importEndedAt = "None"
    if 'csv_attachments' in item.keys():
        csvFilename = item['csv_attachments'][0]['filename']
        csvUrl = item['csv_attachments'][0]['url']
    else:
        csvFilename = 'None'
        csvUrl = 'None'
    imports.append([item['id'], item['workflow_state'], item['user']['login_id'], csvFilename, importCreatedAt, importStartedAt, importEndedAt, csvUrl])
print(f'=== Most recent 10 SIS uploads for Canvas {envLabel}')
print(columnar(imports, importsHeader, no_borders=True))
print('')
