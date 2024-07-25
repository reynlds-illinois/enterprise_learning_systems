#!/usr/bin/python
#
import sys, os, json, csv, requests, time, datetime
from datetime import date
from columnar import columnar
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
from pprint import pprint
print('')
#
realm = realm()  # choose between PROD, BETA, TEST
print(f'Connected to {realm["envLabel"]} - {realm["canvasUrl"]}')
print('')
canvasApi = realm['canvasApi']
canvasUrl = realm['canvasUrl']
canvasToken = realm['canvasToken']
authHeader = {"Authorization": f"Bearer {canvasToken}"}
canvasTerms = realm['canvasTerms']
canvasAccountID = realm['canvasUrbanaID']
canvasUserID = 'F'
searchResults = []
enrollRestoreSelection = 'x' ###
sectionExtendSelection = 'x'
enrollmentNewStatus = 'x'
yesNo = 'x'
GTG = 1
status = 'x'
termID = ''
eRRors = 0
canvasEnrollIDs = [] ###
canvasSectionIDs = []
canvasSectionID = ''
while canvasUserID == "F":
    netID = input("Enter the NetID of the user requiring extension: ")
    canvasUserID = canvasGetUserInfo(netID)[0]
    if canvasUserID != "F":
        continue
    else:
        print("That user is not found. Please try again.")
print('')
#
while termID not in canvasTerms:
    termID = input("Banner Term Code (leave blank for 'all'): ").upper()
    if termID == '':
        break
if not termID:
    enrollmentsUrl = f"{canvasApi}users/{canvasUserID}/enrollments"
    tempTermID = 'ALL'
else:
    enrollmentsUrl = f"{canvasApi}users/{canvasUserID}/enrollments?enrollment_term_id=sis_term_id%3A{termID}"
    tempTermID = termID
print('')
while status != 'a' and status != 'i' and status != 'd' and status != 'c' and status != 'v' and status != '':
    status = input("Enrollment status:  (a)ctive, (c)ompleted, (d)eleted, (i)nactive, in(v)ited, <enter> for all: ")
    print('')
if status == "a": status = ["active"]
elif status == "c": status = ["completed"]
elif status == "d": status = ["deleted"]
elif status == "i": status = ["inactive"]
elif status == "v": status = ["invited"]
else: status = ["active", "inactive", "deleted", "completed", "invited"]
print("")
#
for item in status:
    params = {"per_page": 100, "state":f"{item}"}
    response = requests.get(enrollmentsUrl, headers=authHeader, params=params)
    if len(response.json()) > 0:
        searchResults.extend(response.json())
        while 'next' in response.links:
            response = requests.get(response.links['next']['url'], headers=authHeader, params=params)
            searchResults.extend(response.json())
if len(searchResults) == 0:
    print(f"No {status} courses found for user {netID} in term {tempTermID}.")
    print('')
else:
    searchResults = canvasJsonDates(searchResults)
    #
    tableTemp = []
    canvasSectionIDs = []
    columnHeaders = ['canvas_id', 'enroll_id', 'net_id', 'course_id', '>SECTION_ID<', 'c_section_id', 'role', 'status']
    #
    for row in searchResults:
        if row['sis_section_id'] is not None:
            tableTemp.append([row['course_id'], str(row['id']), row['sis_user_id'], row['sis_course_id'], row["sis_section_id"], int(row["course_section_id"]), row['role'], row['enrollment_state']])
            canvasSectionIDs.append(str(row['sis_section_id']))
        else: continue
    #
    table = columnar(tableTemp, columnHeaders, no_borders=True)
    print(table)
    #
    while sectionExtendSelection not in canvasSectionIDs:
        print()
        sectionExtendSelection = str(input("Section ID to extend: "))
        print()
    #
    for row in tableTemp:
        if row[4] == sectionExtendSelection:
            print('>>> New Section End Date - ',end='')
            sectionEndDate = getDate()
            sectionEndDate = f"{sectionEndDate}T00:00:00"
            newSectionSisID = f"{row[4]}_ext"
            canvasCourseID = row[0]
            getTeachersURL = f"{canvasApi}courses/{canvasCourseID}/enrollments"
            getTeachersParams = {"type":"TeacherEnrollment",
                                 "state":"active"}
            teachers = requests.get(getTeachersURL, params=getTeachersParams, headers=authHeader).json()
            if len(teachers) != 0:
                courseTeachers = []
                for item in teachers:
                    courseTeachers.append(item['user']['id'])
            else:
                print("No Teachers Identified for this course")
                print()
            break
        else:
            continue
    #
    print()
    print(f'NetID:                 {netID}')
    print(f'Current Section:       {row[4]}')
    print(f'New Section to create: {newSectionSisID}')
    print(f'Enrollment End Date:   {sectionEndDate}')
    print(f'Teacher(s):            {courseTeachers}')
    print()
    #
    while yesNo != 'y' and yesNo != 'n':
        yesNo = input("Proceed (y/n)?  ").lower().strip()
        print()
    print()
#
    if yesNo == 'y':
        while eRRors == 0:
            try:
                print('= Creating New Section...')
                newSectionParams = {"course_section[name]":newSectionSisID,
                                    "course_section[sis_section_id]":newSectionSisID,
                                    "course_section[end_at]":sectionEndDate,
                                    "course_section[restrict_enrollments_to_section_dates]":True}
                addSectionUrl = f"{canvasUrl}/api/v1/courses/{canvasCourseID}/sections"
                createSection = requests.post(addSectionUrl, headers=authHeader, params=newSectionParams).json()
                print('= New section created...')
                print()
            except Exception as e:
                print(f"!!! Error: {e}")
                input('> ENTER to continue...')
                print()
                eRRors += 1
            try:
                print('= Enrolling Students In New Section...')
                newSectionID = createSection['id']
                enrollUserUrl = f"{canvasUrl}/api/v1/sections/{newSectionID}/enrollments"
                enrollStudentParams = {"enrollment[user_id]":canvasUserID,
                                       "enrollment[type]":"StudentEnrollment",
                                       "enrollment[notify]":False}
                enrollUser = requests.post(enrollUserUrl, headers=authHeader, params=enrollStudentParams).json()
                print("= Student enrolled in new section.")
                print()
            except Exception as e:
                print(f"!!! Error: {e}")
                input('> ENTER to continue...')
                print()
                eRRors += 1
            try:
                print('= Enrolling Teachers in New Section')
                for item in courseTeachers:
                    enrollTeacherParams = {"enrollment[user_id]":item,
                                           "enrollment[type]":"TeacherEnrollment",
                                           "enrollment[notify]":False}
                    enrollUser = requests.post(enrollUserUrl, headers=authHeader, params=enrollTeacherParams).json()
                print('= Teacher(s) successfully enrolled in new section.')
                print()
                print('>>> Student enrollment has been successfully extended')
                print()
                break
            except Exception as e:
                print(f"Error: {e}")
                input('> ENTER to continue...')
                print()
                eRRors += 1
    else:
        print("Nothing to do. Exiting...")
        print()
print(f">>> CLOSING CONNECTION TO {canvasUrl} <<<")
print()
