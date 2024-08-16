#!/usr/bin/python
#
import sys, os, requests, pprint, urllib, json, time, datetime
from datetime import date, datetime, timedelta
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import findCanvasCourse
#
realm = realm()
#
sleepDelay = 2
yesNo = ''
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
params = {"per_page": 100}
authHeader = {"Authorization": f"Bearer {canvasToken}"}
netID = input('Please enter the NetID of the Teacher for enrollment:  ')
canvasUserID = canvasGetUserInfo(netID)[0]
print()
uiucCourseID = input('Please enter the course ID to which they will be enrolled:  ')
canvasCourseID = findCanvasCourse(uiucCourseID)
canvasCourseInfo = requests.get(f"{canvasApi}courses/{canvasCourseID}", headers=authHeader).json()
canvasCourseID = canvasCourseInfo['id']
canvasCourseName = canvasCourseInfo['name']
courseURL = f"{canvasApi}courses/{canvasCourseID}"
enrollURL = f"{courseURL}/enrollments"
print()
dateFormat = "%Y-%m-%dT%H:%M:%S"
env = ''
print()
print(f'Connected to:  {canvasApi}')
print()
print("|=== ENROLLMENT SUMMARY ===")
print("|")
print(f"| NetID:       {netID}")
print(f"| Course ID:   {uiucCourseID}")
print(f"| End Date:    {canvasCourseInfo['end_at']}")
print(f"| Course Name: {canvasCourseName}")
print("|")
print("| ========================")
print()
while yesNo != 'y' and yesNo != 'n':
    yesNo = input("> Proceed? (y/n)  ").lower()[0]
    print()
if yesNo == 'n':
    print("No changes made...Exiting.")
    print()
else:
    try:
        # prep date info
        endDate = canvasCourseInfo['end_at']
        #centralEndDate = datetime.datetime(endDate, dateFormat)
        newEndDate = datetime.now() + timedelta(hours=1)
        newEndDate = newEndDate.strftime(dateFormat)
        courseParams = {"course[end_at]":newEndDate}
        # update end date temporarily
        courseDateChange = requests.put(courseURL, headers=authHeader, params=courseParams)
        print("> Course date successfully updated.")
        time.sleep(sleepDelay)
        print()
        enrollParams = {"enrollment[user_id]":canvasUserID,
                        "enrollment[type]":"TeacherEnrollment",
                        "enrollment[state]":"active"}
        # enroll user as teacher in course
        requests.post(enrollURL, headers=authHeader, params=enrollParams)
        print("> Successfully enrolled teacher in course.")
        time.sleep(sleepDelay)
        print()
        courseParams = {"course[end_at]":endDate}
        # configure course end date to original
        courseDateChange = requests.put(courseURL, headers=authHeader, params=courseParams)
        print("> Course date successfully set back to original.")
        print()
        time.sleep(sleepDelay)
        print(f">>> Share this URL with the requestor:  {realm['canvasUrl']}/courses/{canvasCourseID}")
        print()
    except Exception as e:
        print(f"> Error: {e}")
        print()
print(f"### Connection to {canvasApi} is closed.")
print()
