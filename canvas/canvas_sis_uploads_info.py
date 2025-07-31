#!/usr/bin/python
#
import sys, os, requests, urllib, json, time, datetime, tzlocal, pytz
from columnar import columnar
from datetime import date
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from columnar import columnar
from canvasFunctions import logScriptStart
from canvasFunctions import canvasJsonDates
#logScriptStart()
realm = realm()
print(f'Connected to {realm["envLabel"]} - {realm["canvasUrl"]}')
#
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
canvasEnvLabel = realm['envLabel']
authHeaders = {"Authorization": f"Bearer {canvasToken}"}
today = str(date.today().strftime("%Y-%m-%d"))
canvasResults = 100.5
importIDs = []
urlDetail = 'r'
timeFormat = "%Y-%m-%d  %H:%M:%S"
importsHeader = ['ID', 'STATE', 'USER', 'FILE','CREATED', 'STARTED', 'ENDED']
while True:
    try:
        print()
        canvasResults = int(input('How many results to view: '))
        if canvasResults > 0 and canvasResults < 51:
            break
        else:
            print('> Too large. Please enter a whole number from 1 to 50.')
    except ValueError:
        print('> Not an integer. Please enter a whole number from 1 to 50.')
print()
params = {"per_page":canvasResults}
sisUrl = f"{canvasApi}accounts/1/sis_imports"
#
def canvasSISUploads(sisUrl, params, authHeaders):
    imports = []
    print('')
    #
    r = requests.get(sisUrl, params=params, headers=authHeaders).json()
    r = canvasJsonDates(r)
    for item in r['sis_imports']:
        if item['started_at']:
            #importStartedAt = item['started_at'].replace("T"," ").replace("Z","")
            importStartedAt = item['started_at']
        else:
            importStartedAt = "None"
        if item['created_at']:
            importCreatedAt = item['created_at']
            #importCreatedAt = item['created_at'].replace("T"," ").replace("Z","")
        else:
            importCreatedAt = "None"
        if item['ended_at']:
            importEndedAt = item['ended_at']
            #importEndedAt = item['ended_at'].replace("T"," ").replace("Z","")
        else:
            importEndedAt = "None"
        if 'csv_attachments' in item.keys():
            csvFilename = item['csv_attachments'][0]['filename']
            csvUrl = item['csv_attachments'][0]['url']
        else:
            csvFilename = 'None'
            csvUrl = 'None'
        imports.append([item['id'], item['workflow_state'], item['user']['login_id'], csvFilename, importCreatedAt, importStartedAt, importEndedAt])
        importIDs.append(str(item['id']))
    #
    print()
    print(f'> Most recent {canvasResults} SIS uploads for Canvas {canvasEnvLabel}')
    print(columnar(imports, importsHeader, no_borders=True))
    print()
#
while True:
    canvasSISUploads(sisUrl, params, authHeaders)
    print()
    urlDetail = input("Choose ID for additional detail, 'r' to refresh or 'q' to quit: ").strip()
    print()
    if urlDetail == 'q':
        print('Exiting without changes...')
        break
    elif urlDetail == 'r':
        continue  # refresh listing
    elif urlDetail in importIDs:
        importUrl = f"{sisUrl}/{urlDetail}"
        r = requests.get(importUrl, headers=authHeaders).json()
        r = canvasJsonDates(r)
        print(f'=== DETAILS FOR IMPORT ID {urlDetail} ===')
        print()
        pprint(r)
        break
        print()
    else:
        print('Invalid input. Please enter a valid SIS ID, "r" to refresh, or "q" to quit.')
        print()
