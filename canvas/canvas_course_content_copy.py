#!/usr/bin/python
# 
import sys, requests, csv, time, json, time
from datetime import date
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm, logScriptStart
#logScriptStart()
copyWorkflowStates = ['queued', 'pre-processing', 'pre-processed', 'running', 'waiting_for_select']
realm = realm()
def findCanvasCourse(courseId):
    """Return Canvas course ID when UIUC course ID is provided"""
    import csv
    from pprint import pprint
    csv_file = csv.reader(open("/var/lib/canvas-mgmt/config/canvas_courses.csv", "r", encoding="utf-8"), delimiter=",")
    for row in csv_file:
        if courseId == row[1]:
            print()
            print(f'  > Canvas Course ID:   {row[0]}')
            print(f'  > UIUC Course ID:     {row[1]}')
            print(f'  > UIUC Course Title:  {row[4]}')
            print(f'  > Canvas Sub-Account: {row[6]}')
            print(f'  > Banner Term ID:     {row[8]}')
            print(f'  > Course Created:     {row[10]}')
            print(f'  > Course Status:      {row[9]}')
            print()
            return row
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
canvasURL = canvasApi.strip('/api/v1/')
canvasAuth = {"Authorization": f"Bearer {canvasToken}"}
params = {"per_page": 100}
yesNoOptions = ['y', 'n']
yesNo = ''
sourceCourse = input('> Enter the UIUC course ID to use as copy source: ')
canvasSourceCourseID = findCanvasCourse(sourceCourse)[0]
print()
targetCourse = input('> Enter the UIUC course ID to use as the copy target: ')
canvasTargetCourseID = findCanvasCourse(targetCourse)[0]
print()
while yesNo not in yesNoOptions:
    yesNo = input(f'> Copy course content from {sourceCourse} to {targetCourse} (y/n)? ').lower()[0]
print()
if yesNo == 'n':
    print('>>> No changes made. Exiting. <')
    print()
    sys.exit()
else:
    resetCourse = ''
    while resetCourse not in yesNoOptions:
        resetCourse = input('> Reset target course first (y/n)? ').lower()[0]
        print()
    if resetCourse == 'y':
        print('>>> Resetting target course before copy...')
        print()
        resetCourseURL = f'{canvasApi}courses/{canvasTargetCourseID}/reset_content'
        resetResponse = requests.post(resetCourseURL, headers=canvasAuth)
        #time.sleep(5)
        if resetResponse.status_code == 200 or resetResponse.status_code == 201:
            canvasTargetCourseID = resetResponse.json()['id']
            print(f'### Target course reset successfully. New Canvas Course ID captured:  {canvasTargetCourseID}')
    print()
    print(f'>>> Content copy proceeding...')
    print()
    copyURL = f'{canvasApi}courses/{canvasTargetCourseID}/content_migrations'
    copyData = {
        "migration_type": "course_copy_importer",
        "settings[source_course_id]": canvasSourceCourseID,
    }
    copyResponse = requests.post(copyURL, headers=canvasAuth, data=copyData)
    if copyResponse.status_code == 200 or copyResponse.status_code == 201:
        print('### Course content copy initiated successfully.')
        copyID = copyResponse.json()['id']
        progressURL = copyResponse.json()['progress_url']
        copyStatus = json.loads(requests.get(progressURL, headers=canvasAuth).text)
        while copyStatus['workflow_state'] in copyWorkflowStates:
            print(f'  > Copy status: {copyStatus["workflow_state"]}...waiting for recheck...')
            time.sleep(5)
            copyStatus = json.loads(requests.get(progressURL, headers=canvasAuth).text)
        print()
        print(f'### Final copy status: {copyStatus["workflow_state"]}.')
        print()
        print(f'### New target course location:  {canvasURL}/courses/{canvasTargetCourseID}')
        print()
    else:
        print(f'  > ERROR: Course content copy failed with status code {copyResponse.status_code}.')
    print()
