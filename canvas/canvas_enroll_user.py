#!/usr/bin/python
#
import sys, os, requests, pprint, urllib, json, time, datetime
from datetime import date, datetime, timedelta, timezone
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import findCanvasCourse
from canvasFunctions import findCanvasSection
from canvasFunctions import findCanvasSections
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
    canvasCourseName = canvasCourseInfo['name']
    print()
    while newRole != 't' and newRole != 's' and newRole != 'a' and newRole != 'o':
        newRole = input("Enter course role: (t)eacher, (s)tudent, T(a) or (o)bserver: ").lower()[0]
        print()
    if newRole == 'o':
        newRole = "ObserverEnrollment"
        sectionID = 'n/a'
        enrollURL = f"{canvasApi}courses/{canvasCourseID}/enrollments"
    elif newRole == 't':
        newRole = "TeacherEnrollment"
        sectionID = 'n/a'
        enrollURL = f"{canvasApi}courses/{canvasCourseID}/enrollments"
    elif newRole == 's':
        courseSections = findCanvasSections(uiucCourseID)
        courseSectionsList = []
        newRole = "StudentEnrollment"
        sectionID = ''
        print("# Course Sections")
        for section in courseSections:
            courseSectionsList.append(section[0])
            if not section[1]:
                sectionSISID = '##### BASE COURSE SHELL #####'
            else:
                sectionSISID = section[1]
            canvasSectionID = section[0]
            sectionName = section[5]
            print(f"  #   - Section ID: {canvasSectionID} <<<")
            print(f"  #     Section SIS ID: {sectionSISID}")
            print(f"  #     Section Name: {sectionName}")
            print()
        while sectionID not in courseSectionsList:
            sectionID = input("  > Enter the Section ID of the target course: ")
            #canvasSectionID = findCanvasSection(sectionID)
            enrollURL = f"{canvasApi}sections/{sectionID}/enrollments"
    else:
        newRole = "TaEnrollment"
        sectionID = 'n/a'
        enrollURL = f"{canvasApi}courses/{canvasCourseID}/enrollments"
    #
    #canvasCourseID = canvasCourseInfo['id']
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
    print(f"| Enroll URL:  {enrollURL}")
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
            # Parse endDate and get now in UTC
            endDateDT = datetime.strptime(endDate, "%Y-%m-%dT%H:%M:%SZ") if endDate else None
            if endDateDT is not None:
                # Make endDateDT timezone-aware (UTC)
                endDateDT = endDateDT.replace(tzinfo=timezone.utc)
            nowUTC = datetime.now(timezone.utc)
            updatedEndDate = False
            if endDateDT is not None and endDateDT < nowUTC:
                # Only update if course has ended (endDate exists and is before now)
                newEndDate = nowUTC + timedelta(hours=1)
                newEndDateStr = newEndDate.strftime("%Y-%m-%dT%H:%M:%SZ")
                courseParams = {"course[end_at]": newEndDateStr}
                courseDateChange = requests.put(courseURL, headers=authHeader, params=courseParams)
                print("> Course date successfully updated.")
                time.sleep(sleepDelay)
                print()
                updatedEndDate = True
            enrollParams = {"enrollment[user_id]":canvasUserID,
                            "enrollment[type]":newRole,
                            "enrollment[enrollment_state]":"active",
                            "enrollment[notify]":"false"}
            # enroll user as teacher in course
            #print(f'enrollParams: {enrollParams}')
            r = requests.post(enrollURL, headers=authHeader, params=enrollParams)
            #print(r.text)
            print(f"> Successfully enrolled {newRole} in course.")
            time.sleep(sleepDelay)
            print()
            if updatedEndDate:
                # Only reset end date if it was changed
                courseParams = {"course[end_at]": endDate}
                courseDateChange = requests.put(courseURL, headers=authHeader, params=courseParams)
                print("> Course date successfully set back to original.")
                print()
                time.sleep(sleepDelay)
            print(f">>> Canvas course URL:  {realm['canvasUrl']}/courses/{canvasCourseID}")
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
