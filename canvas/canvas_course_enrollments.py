#!/usr/bin/python
#
import sys, os, json, csv, requests, time, datetime
from datetime import date
from columnar import columnar
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
from pprint import pprint
print()
print('=== Please note that this pulls directly from Canvas PROD only! ===')
print()
realm = getEnv()
canvasApi = realm['canvas.api-prod']
canvasUrl = canvasApi.strip('api/v1/')
canvasToken = realm['canvas.write-token']
authHeader = {"Authorization": f"Bearer {canvasToken}"}
canvasTerms = realm['canvas.terms'].split(',')
canvasAccountID = '1'
searchResults = []
canvasEnrollIDs = []
status = ["active", "inactive", "deleted", "completed", "invited"]
#
courseID = input(">>> Enter the Course ID of the target course: ")
canvasCourseID = findCanvasCourse(courseID)
enrollmentsUrl = f"{canvasApi}courses/{canvasCourseID}/enrollments"
#
for item in status:
    params = {"per_page": 100, "state":f"{item}"}
    response = requests.get(enrollmentsUrl, headers=authHeader, params=params)
    if len(response.json()) > 0:
        searchResults.extend(response.json())
        while 'next' in response.links:
            response = requests.get(response.links['next']['url'], headers=authHeader, params=params)
            searchResults.extend(response.json())
#
if len(searchResults) > 0:
    searchResults = canvasJsonDates(searchResults)
    tableTemp = []
    columnHeaders = ['enroll_id', 'net_id', 'uin', 'course_id', 'section_id', 'role', 'status', 'created']
    for row in searchResults:
        if row['sis_user_id'] and row['user']['integration_id']:
            tableTemp.append([row['id'], row['sis_user_id'], row['user']['integration_id'], row['sis_course_id'], row['sis_section_id'], row['role'].replace('Enrollment',''), row['enrollment_state'], row['created_at']])
            canvasEnrollIDs.append(str(row['id']))
        else:
            continue
    table = columnar(tableTemp, columnHeaders, no_borders=True)
    print(table)
else:
    print()
    print(f'No results found for Course ID:  {courseID}')
print()
