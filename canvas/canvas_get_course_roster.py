#!/usr/bin/python
#
import sys, os, requests, urllib, json, time, datetime
from datetime import date
from columnar import columnar
from canvasFunctions import *
env = getEnv()
logScriptStart()
canvasApi = env["canvas.api-prod"]
canvasToken = env["canvas.ro-api"]
headers = {"Authorization": f"Bearer {canvasToken}"}
params = {"per_page": 100}
canvasAccountId = "1"
students = 0
nonStudents = 0
maxUsernameLength = 35
today = str(date.today().strftime("%Y-%m-%d"))
#
print('')
courseId = input("Enter the CourseID of the target course: ")
canvasCourseId = findCanvasCourse(courseId)
enrollUrl = f"{canvasApi}courses/{canvasCourseId}/enrollments"
columnHeaders = ['sis_course_id', 'login_id', 'role']
#
response = requests.get(enrollUrl, headers=headers, params=params)
#
if len(response.json()) == 0:
    print(f"Roster unavailable for:  {courseId}")
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
            tableTemp.append([searchResults[item]['sis_course_id'], searchResults[item]['user']['login_id'], searchResults[item]['role'].replace('Enrollment','')])
    table = columnar(tableTemp, columnHeaders, no_borders=True)
    print(table)
    print("Students:     ", students)
    print("Non-students: ", nonStudents)
    print('')
