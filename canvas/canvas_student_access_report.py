#!/usr/bin/python
#
import sys, os, json, csv, requests, time, datetime
from pprint import pprint
from datetime import date
from datetime import datetime
from columnar import columnar
from boxsdk import JWTAuth, Client
from boxsdk.exception import BoxAPIException
from boxsdk.object.collaboration import CollaborationRole
sys.path.append("/var/lib/canvas-mgmt/bin")     # working sys path
from canvasFunctions import realm               # choose the environment in which to work
from canvasFunctions import findCanvasCourse    # convert UIUC course ID to Canvas course ID
from canvasFunctions import canvasGetUserInfo   # convert UIUC NetID to Canvas user ID
from canvasFunctions import getDate             # a date specifically formatted for YEAR-MO-DA
from canvasFunctions import canvasJsonDates
from canvasFunctions import logScriptStart
logScriptStart()
print('')
#
now = int(time.time())
realm = realm()
print(f'Connected to {realm["envLabel"]} - {realm["canvasUrl"]}')
print('')
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
authHeader = {"Authorization": f"Bearer {canvasToken}"}
#boxAuth = JWTAuth.from_settings_file('/var/lib/canvas-mgmt/config/box_canvas_integration.json')
boxAuth = JWTAuth.from_settings_file('/var/lib/canvas-mgmt/config/83165_6no30ljy_config.json')
boxClient = Client(boxAuth)
columnHeaders = ['TYPE', 'DATE/TIME', 'ACTION(S)']
csvPath = '/var/lib/canvas-mgmt/reports/'
netID = 'False'
courseID = 'False'
yesNo = 'x'
uploadToBox = 'x'
#
while uploadToBox != 'y' and uploadToBox != 'n':
    uploadToBox = input('>>> Upload and share these results on BOX (y/n)? ').lower().strip()
    print()
if uploadToBox == 'y':
    tdxTicket = input('Enter the TDX ticket (only numbers): ')
    print()
    requestorNetID = input('Enter the NetID of the TDX requestor: ')
    print()
    requestorEmailAddress = f'{requestorNetID}@illinois.edu'
    boxParentFolderID = '145486921579'
    boxRequstorRole = 'Viewer'
    tempFolderName = f'tdx_{tdxTicket}'
else: tdxTicket = time.time()
tempFileName = f'tdx_{tdxTicket}_access_report.csv'
tempFilePath = f'{csvPath}{tempFileName}'
print()
#
while netID == 'False':
    netID = input('Enter the NetID of the student: ')
    print()
canvasUserID = canvasGetUserInfo(netID)[0]
while courseID == 'False':
    courseID = input('Enter the UIUC Course ID of the course: ')
    print()
canvasCourseID = findCanvasCourse(courseID)
#
#
#
pvList = []
partList = []
accessList = []
url = f'{canvasApi}courses/{canvasCourseID}/analytics/users/{canvasUserID}/activity'
r = requests.get(url, headers=authHeader)
if r.status_code == 200:
    r = r.json()
#
if len(r) > 0:
    r = canvasJsonDates(r)
    accessList.append(columnHeaders)
    if len(r['page_views']) > 0:
        for item in r['page_views']:
            pvList.append(item)
        for item in pvList:
            accessList.append(['page-views', item, r['page_views'][item]])
    if len(r['participations']) > 0:
        for item in r['participations']:
            accessList.append(['participation', item['created_at'], item['url']])
#
for item in accessList:     # Fixup date formatting/TZ
    if item[0] == 'page-views':
        date_string_with_offset = item[1]
        # Parse the date string, including the offset
        datetime_object = datetime.fromisoformat(date_string_with_offset)
        # Remove the time offset
        datetime_object_no_offset = datetime_object.replace(tzinfo=None)
        # Format the datetime object back to a string, if needed
        date_string_no_offset = datetime_object_no_offset.strftime("%Y-%m-%d")
        # replace original with newly formatted date
        item[1] = item[1].replace(item[1], date_string_no_offset)
#
accessList = sorted(accessList, key=lambda x: x[1], reverse=True)
accessTable = columnar(accessList, no_borders=True)
print('===== STUDENT ACCESS SUMMARY ======')
print(accessTable)
print('===================================')
print()
#
#while yesNo != 'y' and yesNo != 'n':
#    yesNo = input('>>> Proceed with upload to BOX (y/n)? ').strip().lower()
#
print()
#if yesNo == 'y':
try:    # write table to local CSV
    with open(tempFilePath, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(accessList)
        writer.writerow(['===== USER/COURSE INFO ====='])
        writer.writerow([f' - Student NetID: {netID}'])
        writer.writerow([f' - Course ID: {courseID}'])
    print(f'= Successfully report to CSV: {tempFilePath}')
except Exception as e:
    print(f'!!! Error: {e}')
    print()
    #
try:
    if uploadToBox == 'y':
        while yesNo != 'y' and yesNo != 'n':
            yesNo = input('>>> Proceed with upload to BOX (y/n)? ').strip().lower()
            print()
        try:
            # create target folder in BOX
            boxCreateTargetFolder = boxClient.folder(boxParentFolderID).create_subfolder(tempFolderName)
            boxTargetFolderID = int(boxCreateTargetFolder['id'])
            print('= Successfully created the BOX target folder.')
            print()
            # upload local CSV file to new BOX target folder
            r = boxClient.folder(boxTargetFolderID).upload(tempFilePath, tempFileName)
            print(r)
            print('= Successfully uploaded the CSV to BOX.')
            # share new BOX target folder with TDX requestor
            x = boxClient.folder(boxTargetFolderID).collaborate_with_login(requestorEmailAddress,CollaborationRole.VIEWER)
            boxSharedLink = f'https://uofi.box.com/folder/{boxTargetFolderID}'
            print()
            print('=====================================')
            print('==')
            print(f'== Folder successfully shared in BOX:  {boxSharedLink}')
            print('==')
            print('=====================================')
        except Exception as e:
            print(f'!!! Error During BOX Actions: {e}')
except Exception as e:
    print(f'!!! Error: {e}')
    print()
print()
print(f'>>> Exiting {canvasApi}...')
print()
