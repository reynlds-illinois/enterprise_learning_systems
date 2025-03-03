#!/usr/bin/python
#
import csv, json, os, sys, requests
import time, datetime
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
from itertools import chain
from pprint import pprint
realm = realm()
envLabel = realm['envLabel']
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
print('')
print(f'Connected to {envLabel} on {canvasApi}')
print('')
authHeader = {"Authorization": f"Bearer {canvasToken}"}
now = int(time.time())
filePath = '/var/lib/canvas-mgmt/reports/'
exportType = ''
yesNo = ''
fileExt = ''
sleepDelay = 5
#
sisCourseID = input('Enter the UIUC course ID for export: ').lower()
canvasCourseID = findCanvasCourse(sisCourseID)
print()
while exportType != 'c' and exportType != 'q' and exportType != 'z':
    exportType = input('What type of export? (c)ommon cartridge, (q)ti, (z)ip ').lower().strip()[0]
    print()
if exportType == 'c':
    exportType = 'common_cartridge'
    fileExt = '.cc'
elif exportType == 'q':
    exportType = 'qti'
    fileExt = '.qti'
else:
    exportType = 'zip'
    fileExt = '.zip'
#
while yesNo != 'y' and yesNo != 'n':
    yesNo = input(f'Proceed with export of {sisCourseID} in {exportType} format (y/n)? ').lower().strip()[0]
    print()
if yesNo == 'y':
    print('Exporting the course...')
    print()
    targetFilePath = f'{filePath}{sisCourseID}-course_export-{now}{fileExt}'
    courseExportURL = f'{canvasApi}courses/{canvasCourseID}/content_exports'
    courseExportParams = {'export_type':exportType,
                          'skip_notifications':True}
    contentExport = requests.post(courseExportURL, headers=authHeader, params=courseExportParams)
    if contentExport.status_code == 200:
        contentExport = contentExport.json()
        exportID = contentExport['id']
        exportProgressURL = f'{canvasApi}courses/{canvasCourseID}/content_exports/{exportID}'
        exportStatus = requests.get(exportProgressURL, headers=authHeader).json()
        while exportStatus['workflow_state'] != 'exported':
            print('>>> Waiting for course export completion...')
            exportStatus = requests.get(exportProgressURL, headers=authHeader).json()
            time.sleep(sleepDelay)
            print()
        downloadURL = exportStatus['attachment']['url']
        contentFile = requests.get(downloadURL, headers=authHeader)
        with open(targetFilePath, 'wb') as f:
            f.write(contentFile.content)
        print()
        print(f'=== Course export SUCCESSFUL. Export saved here: {targetFilePath}')
        print()
        print(f'### Exiting {envLabel}...')
        print()
else:
    print()
    print(f'### Exiting {envLabel} without changes...')
print()
