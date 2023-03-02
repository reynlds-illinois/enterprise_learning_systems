#!/usr/bin/python

import sys, os, requests, urllib, json, time, datetime
from datetime import date
from columnar import columnar
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
env = getEnv()
#logScriptStart()
canvasApi = env["canvas.api-prod"]
canvasToken = env["canvas.ro-api"]
headers = {"Authorization": f"Bearer {canvasToken}"}
params = {"per_page": 100}
canvasAccountId = "1"
workflowState = ''
#params = {"per_page": 100, }
canvasAccountId = "1"
students = 0
nonStudents = 0
maxUsernameLength = 35
today = str(date.today().strftime("%Y-%m-%d"))
#
print('')
courseId = input("Enter the CourseID of the target course: ")
print('')
print("Enter enrollment state: (a)ctive,")
print("                        (i)nvited,")
print("                        (c)completed,")
print("                        (d)eleted")
while workflowState != 'a' and workflowState != 'i' and workflowState != 'c' and workflowState != 'd':
    workflowState = input("                       > ").lower()[0]
if workflowState == 'a': workflowState = 'active'
elif workflowState == 'i': workflowState = 'invited'
elif workflowState == 'c': workflowState = 'completed'
else: workflowState = 'deleted'
print('')
#
params = {"per_page": 100, "state": f"{workflowState}"}
#
canvasCourseId = findCanvasCourse(courseId)
enrollUrl = f"{canvasApi}courses/{canvasCourseId}/enrollments"
columnHeaders = ['course_id', 'section_id', 'net_id', 'role', 'current_grade']
#
response = requests.get(enrollUrl, headers=headers, params=params)
#
if len(response.json()) == 0:
    print(f"No {workflowState} enrollments found for:  {courseId}")
else:
    tableTemp = []
    searchResults = response.json()
    while 'next' in response.links:
        response = requests.get(response.links['next']['url'], headers=headers, params=params)
        searchResults.extend(response.json())
    for item in range(0, len(searchResults)):
        if len(searchResults[item]["user"]["login_id"]) > maxUsernameLength:
            continue
        else:
            if searchResults[item]["role"] == "StudentEnrollment":
                students += 1
            else:
                nonStudents += 1
            #print(paginatedSearchResults[item]["sis_course_id"] + "|" + paginatedSearchResults[item]["user"]["login_id"] + "|" + paginatedSearchResults[item]["role"])
            tableTemp.append([searchResults[item]['sis_course_id'], searchResults[item]['sis_section_id'],searchResults[item]['user']['login_id'], searchResults[item]['role'].replace('Enrollment','')])
    table = columnar(tableTemp, columnHeaders, no_borders=True)
    print(table)
    print(f"Stats for {workflowState} enrollments: ")
    print("  Students:     ", students)
    print("  Non-students: ", nonStudents)
    print('')
