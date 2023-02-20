#!/usr/bin/python
import os, sys, requests, urllib, json, time, datetime
from datetime import date
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt//bin")
from canvasFunctions import *
envDict = getEnv()
env = 'x'
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower()[0]
    if env == 'p':
        canvasApi = envDict["canvas.api-prod"]
        canvasToken = envDict["canvas.write-token"]
        envLabel = "PROD"
    else:
        canvasApi = envDict["canvas.api-beta"]
        canvasToken = envDict["canvas.write-token"]
        envLabel = "STAGE"
canvasAccountId = "1"
headers = {"Authorization": f"Bearer {canvasToken}"}
today = str(date.today().strftime("%Y-%m-%d"))
roleInput = ''
courseRole = ''
sectionID = ''
courseID = ''
choice = ''
logScriptStart()
print('')
#
netId = input("Enter the NetID of the user to enroll: ").lower()
canvasUserId = findCanvasUser(netId)
print('')
while roleInput !="s" and roleInput != "t" and roleInput != "a":
    roleInput = input("Enter the course role to assign...(s)tudent, (t)eacher or t(a): ").lower().strip()
print('')
if roleInput == "s":
    courseRole = "StudentEnrollment"
    sectionID = input("Enter the Section ID of the target course: ")
    canvasSectionID = findCanvasSection(sectionID)
    enrollURL = f"{canvasApi}sections/{canvasSectionID}/enrollments"
elif roleInput == "t":
    courseRole = "TeacherEnrollment"
    courseID = input("Enter the Course ID of the target course: ")
    canvasCourseID = findCanvasCourse(courseID)
    enrollURL = f"{canvasApi}courses/{canvasCourseID}/enrollments"
else:
    courseRole = "TaEnrollment"
    courseID = input("Enter the Course ID of the target course: ")
    canvasCourseID = findCanvasCourse(courseID)
    enrollURL = f"{canvasApi}courses/{canvasCourseID}/enrollments"
#
print('')
params = {
    "enrollment[user_id]": canvasUserId,
    "enrollment[type]": courseRole,
    "enrollment[enrollment_state]": "active",
    "enrollment[notify]": "false"}
#
print("Target enrollment:")
print(f"    canvasUserId: {canvasUserId} ({netId})")
print(f"    courseRole:   {courseRole}")
print(f"    sectionID:    {sectionID}")
print(f"    courseID:     {courseID}")
#print(f"    enrollURL:    {enrollURL}")
print('')
while choice != 'y' and choice != 'n':
    choice = input("Proceed? (y/n) ").lower()
if choice == "y":
    try:
        response = requests.post(enrollURL, headers=headers, params=params)
        print(f"Result:  {response.text}")
    except:
        print(f"Result:  {response.text}")
else:
    print('')
    print("Exiting without changes...")
print('')
