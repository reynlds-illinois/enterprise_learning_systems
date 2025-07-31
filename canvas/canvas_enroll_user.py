#!/usr/bin/python
#
import sys, os, requests, pprint, urllib, json, time, datetime
from datetime import date, datetime, timedelta
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import findCanvasCourse
from canvasFunctions import findCanvasSection
#
realm = realm()
#
sleepDelay = 2
newRole = ''
answer = 'x'
yesNo = ''
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
print(f'Connected to:  {canvasApi}')
params = {"per_page": 100}
authHeader = {"Authorization": f"Bearer {canvasToken}"}
while True:
    print()
    netID = input('Enter the NetID for enrollment:  ')
    canvasUserID = canvasGetUserInfo(netID)[0]
    print()
    uiucCourseID = input('Please enter the course ID to which they will be enrolled:  ')
    canvasCourseID = findCanvasCourse(uiucCourseID)
    canvasCourseInfo = requests.get(f"{canvasApi}courses/{canvasCourseID}", headers=authHeader).json()
    print()
    while newRole != 't' and newRole != 's' and newRole != 'a':
        newRole = input("Enter course role: (t)eacher, (s)tudent or T(a): ").lower()[0]
        print()
    if newRole == 't':
        newRole = "TeacherEnrollment"
        #courseID = input("Enter the Course ID of the target course: ")
        #canvasCourseID = findCanvasCourse(courseID)
        sectionID = 'n/a'
        enrollURL = f"{canvasApi}courses/{canvasCourseID}/enrollments"
    elif newRole == 's':
        newRole = "StudentEnrollment"
        sectionID = input("Enter the Section ID of the target course: ")
        canvasSectionID = findCanvasSection(sectionID)
        enrollURL = f"{canvasApi}sections/{canvasSectionID}/enrollments"
        print(f'canvasSectionID: {canvasSectionID}')
        print(f'enrollURL: {enrollURL}')
    else:
        newRole = "TaEnrollment"
        #courseID = input("Enter the Course ID of the target course: ")
        #canvasCourseID = findCanvasCourse(courseID)
        sectionID = 'n/a'
        enrollURL = f"{canvasApi}courses/{canvasCourseID}/enrollments"
    #
    canvasCourseID = canvasCourseInfo['id']
    canvasCourseName = canvasCourseInfo['name']
    courseURL = f"{canvasApi}courses/{canvasCourseID}"
    #enrollURL = f"{courseURL}/enrollments"
    print()
    dateFormat = "%Y-%m-%dT%H:%M:%S"
    env = ''
    print()
    print("|=== ENROLLMENT SUMMARY ===")
    print("|")
    print(f"| NetID:       {netID}")
    print(f"| Course Role: {newRole}")
    print(f"| Course ID:   {uiucCourseID}")
    print(f"| Section ID:  {sectionID}")
    print(f"| Course Name: {canvasCourseName}")
    print(f"| End Date:    {canvasCourseInfo['end_at']}")
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
                            "enrollment[type]":newRole,
                            "enrollment[enrollment_state]":"active",
                            "enrollment[notify]":"false"}
            # enroll user as teacher in course
            print(f'enrollParams: {enrollParams}')
            r = requests.post(enrollURL, headers=authHeader, params=enrollParams)
            #print(r.text)
            print(f"> Successfully enrolled {newRole} in course.")
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
    #
    print()
    while answer != 'y' and answer != 'n':
        answer = input("Continue with another enrollment (y/n)? ").strip().lower()
    if answer == 'y':
        print()
        answer = 'x'
        yesNo = ''
        continue
    else:
        print()
        break
#
print(f"### Closing connection {canvasApi}...")
print('')
