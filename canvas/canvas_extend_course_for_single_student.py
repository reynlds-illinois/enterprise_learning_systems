#!/usr/bin/python
#
import sys, os, json, csv, requests, time, datetime
from datetime import date
from columnar import columnar
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm               # choose the environment in which to work
from canvasFunctions import findCanvasCourse    # convert UIUC course ID to Canvas course ID
from canvasFunctions import canvasGetUserInfo   # convert UIUC NetID to Canvas user ID
from canvasFunctions import getDate             # a date specifically formatted for YEAR-MO-DA
from canvasFunctions import logScriptStart
from pprint import pprint
logScriptStart()
print('')
#
realm = realm()
print(f'Connected to {realm["envLabel"]} - {realm["canvasUrl"]}')
print('')
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
authHeader = {"Authorization": f"Bearer {canvasToken}"}
canvasUserID = 'X'
canvasCourseID = 'X'
yesNo = 'X'
sectionID = "X"
searchResults = []
tempCourseTeachers = []
courseTeachers = []
sleepDelay = 2
while canvasUserID == "X":
    netID = input("Enter the NetID of the user requiring extension: ")
    canvasUserID = canvasGetUserInfo(netID)[0]
    if canvasUserID != "X":
        continue
    else:
        print("That user is not found. Please try again.")
print()
while canvasCourseID == "X":
    courseID = input("Enter the course that should be extended: ")
    canvasCourseID = findCanvasCourse(courseID)
    if canvasCourseID != "X":
        continue
    else:
        print("That course is not found. Please try again.")
print()
#
studentEnrollments = []
studentHeader = ["Enrollment_ID", "Net_ID", "Course_ID", ">> Section_ID <<"]
courseEnrollmentsUrl = f"{canvasApi}courses/{canvasCourseID}/enrollments"
params = {"per_page": 100}
allCourseEnrollments = requests.get(courseEnrollmentsUrl, headers=authHeader, params=params)
# get all coursle enrollments
if len(allCourseEnrollments.json()) > 0:
    searchResults.extend(allCourseEnrollments.json())
    while 'next' in allCourseEnrollments.links:
        allCourseEnrollments = requests.get(allCourseEnrollments.links['next']['url'], headers=authHeader, params=params)
        searchResults.extend(allCourseEnrollments.json())
#allCourseEnrollments = allCourseEnrollments.json()
allCourseEnrollments = searchResults
for item in allCourseEnrollments:
    if item['role'] == 'TeacherEnrollment':
        tempCourseTeachers.append(item['sis_user_id'])
if len(tempCourseTeachers) >= 1:
    courseTeachers = list(set(tempCourseTeachers))
# identify any student enrollment(s)
print("=== CURRENT ENROLLMENT(S) ===")
print()
for item in allCourseEnrollments:
    if item["user_id"] == int(canvasUserID):
        studentEnrollments.extend([str(item["id"]), item["sis_user_id"], item["sis_course_id"], item["sis_section_id"]])
        print(f"   - Enrollment ID:  {item['id']}")
        print(f"   - NetID:          {item['sis_user_id']}")
        print(f"   - Course ID:      {item['sis_course_id']}")
        print(f"   - Section ID:     {item['sis_section_id']}   <<< USE THIS")
        print()
    else: continue
#if len(studentEnrollments) > 0:
#    # get all teachers from course
#    for item in searchResults:
#        if item['type'] == "TeacherEnrollment":
#            courseTeachers.extend([item["sis_user_id"]])
#print(columnar(studentEnrollments, studentHeader, no_borders=True)
#print()
while sectionID not in studentEnrollments:
    sectionID = input("Enter the Section ID that requires extension: ")
    print()
newExtension = input("Enter the extension or <ENTER> for default (i.e., _ext): ")
if newExtension == '':
    newExtension = "_ext"
newSectionSisID = f"{sectionID}{newExtension}"
print()
sectionEndDate = getDate()
#sectionEndDate = f"{sectionEndDate}T00:00:00"
sectionEndDate = f"{sectionEndDate}T23:59:00"
print()
for item in allCourseEnrollments:
    if str(item["user_id"]) == canvasUserID and item["sis_section_id"] == sectionID:
        print("=== PROPOSED CHANGES ===")
        print()
        print(f"   === Current SectionID:    {sectionID}")
        print(f"   === New Section ID:       {newSectionSisID}")
        print(f"   === New Section End Date: {sectionEndDate}")
        print(f"   === Student NetID:        {netID}")
        print(f"   === Course Teachers:      {courseTeachers}")
        print()
        break
    else: continue
while yesNo != "y" and yesNo != "n":
    yesNo = input("Continue with extension (y/n): ").lower().strip()
    print()
if yesNo == "n":
    print("Exiting. No changes made...")
    print()
else:
    try:
        print('= Creating New Section...')
        newSectionParams = {"course_section[name]":newSectionSisID,
                            "course_section[sis_section_id]":newSectionSisID,
                            "course_section[end_at]":sectionEndDate,
                            "course_section[restrict_enrollments_to_section_dates]":True}
        addSectionUrl = f"{canvasApi}courses/{canvasCourseID}/sections"
        createSection = requests.post(addSectionUrl, headers=authHeader, params=newSectionParams).json()
        print('= New section created...')
        print()
        time.sleep(sleepDelay)
    except Exception as e:
        print(f"!!! Error: {e}")
        input('> ENTER to continue...')
        print()
    try:
        print('= Enrolling Students In New Section...')
        newSectionID = createSection['id']
        enrollUserUrl = f"{canvasApi}sections/{newSectionID}/enrollments"
        enrollStudentParams = {"enrollment[user_id]":canvasUserID,
                               "enrollment[type]":"StudentEnrollment",
                               "enrollment[enrollment_state]":"active",
                               "enrollment[notify]":False}
        enrollUser = requests.post(enrollUserUrl, headers=authHeader, params=enrollStudentParams).json()
        print("= Student enrolled in new section.")
        print()
        time.sleep(sleepDelay)
    except Exception as e:
        print(f"!!! Error: {e}")
        input('> ENTER to continue...')
        print()
    try:
        print('= Enrolling Teachers in New Section')
        for item in courseTeachers:
            canvasTeacherID = canvasGetUserInfo(item)[0]
            enrollTeacherParams = {"enrollment[user_id]":canvasTeacherID,
                                   "enrollment[type]":"TeacherEnrollment",
                                   "enrollment[enrollment_state]":"active",
                                   "enrollment[notify]":False}
            enrollUser = requests.post(enrollUserUrl, headers=authHeader, params=enrollTeacherParams).json()
        print('= Teacher(s) successfully enrolled in new section.')
        print()
        print('>>> Student enrollment has been successfully extended')
        print()
        time.sleep(sleepDelay)
    except Exception as e:
        print(f"Error: {e}")
        input('> ENTER to continue...')
        print()
print(f"Closing connection to {canvasApi}")
print()
