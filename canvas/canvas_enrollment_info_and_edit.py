#!/usr/bin/python
#
import sys, os, json, csv, requests, time, datetime
from datetime import date, datetime, timedelta
from columnar import columnar
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import canvasJsonDates
from canvasFunctions import yesOrNo
from canvasFunctions import canvasCourseInfo
from pprint import pprint
print('')
realm = realm()
print(f'Connected to {realm["envLabel"]} - {realm["canvasUrl"]}')
print('')
canvasApi = realm['canvasApi']
canvasUrl = realm['canvasUrl']
canvasToken = realm['canvasToken']
authHeader = {"Authorization": f"Bearer {canvasToken}"}
canvasTerms = realm['canvasTerms']
canvasAccountID = realm['canvasUrbanaID']
envLabel = realm['envLabel']
dateFormat = "%Y-%m-%dT%H:%M:%S"
sleepDelay = 2
#
def canvasEnrollmentEdit(canvasApi, authHeader, row, enrollmentNewStatus):
    resetDate = 0
    canvasCourseID = row[0]
    courseURL = f"{canvasApi}courses/{canvasCourseID}"
    canvasCourseInfo = requests.get(f'{canvasApi}courses/{canvasCourseID}', headers=authHeader).json()
    now = datetime.now().strftime(format=dateFormat)
    endDate = canvasCourseInfo['end_at']
    if endDate < now:
        print()
        print('>>> Resetting course date for modifications <<<')
        print()
        resetDate = 1
        newEndDate = datetime.now() + timedelta(hours=1)
        #newEndDate = newEndDate.strftime(dateFormat)
        courseParams = {"course[end_at]":newEndDate}
        courseDateChange = requests.put(courseURL, headers=authHeader, params=courseParams)
    time.sleep(sleepDelay)
    params = {"enrollment[user_id]":canvasUserID,
              "enrollment[type]":row[6],
              "enrollment[enrollment_state]":enrollmentNewStatus,
              "enrollment[notify]":False,
              "enrollment[course_section_id]":row[5],
              }
    url = f"{canvasApi}courses/{row[0]}/enrollments"
    print()
    print('>>> Modifying enrollment <<<')
    print()
    enrollModify = requests.post(url, headers=authHeader, params=params).json()
    print('')
    time.sleep(sleepDelay)
    if len(enrollModify) > 1:
        print('> Enrollment successfully changed:')
        print()
        print(f"  NetID:      {enrollModify['sis_user_id']}")
        print(f"  Course ID:  {enrollModify['sis_course_id']}")
        print(f"  Section ID: {enrollModify['sis_section_id']}")
        print(f"  Role:       {enrollModify['type']}")
        print(f"  New State:  {enrollModify['enrollment_state']}")
        print(f"  Date/Time:  {enrollModify['updated_at']}")
        print()
    else:
        print('### Enrollment NOT successfully changed! ###')
        print()
        print(f"  {enrollModify}")
    print('')
    if resetDate == 1:
        print()
        print('>>> Setting course date back to original <<<')
        print()
        courseParams = {"course[end_at]":endDate}
        courseDateChange = requests.put(courseURL, headers=authHeader, params=courseParams)
    time.sleep(sleepDelay)
while True:
    #from canvasFunctions import canvasCourseInfo
    resetDate = 0
    answer = 'x'
    canvasUserID = 'F'
    searchResults = []
    enrollRestoreSelection = 'x'
    enrollmentNewStatus = 'x'
    status = 'x'
    termID = ''
    canvasEnrollIDs = []
    canvasSectionID = ''
    courseStatus = []
    while canvasUserID == "F":
        netID = input("Enter the NetID of the user: ")
        canvasUserID = canvasGetUserInfo(netID)[0]
        if canvasUserID != "F":
            continue
        else:
            print("That user is not found. Please try again.")
    print('')
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
    for item in status:
        params = {"per_page": 100, "state":f"{item}"}
        response = requests.get(enrollmentsUrl, headers=authHeader, params=params)
        if len(response.json()) > 0:
            searchResults.extend(response.json())
            while 'next' in response.links:
                response = requests.get(response.links['next']['url'], headers=authHeader, params=params)
                searchResults.extend(response.json())
    if len(searchResults) > 0:
        searchResults = canvasJsonDates(searchResults)
        tableTemp = []
        columnHeaders = ['course_id', '>ENROLL_ID<', 'net_id', 'sis_course_id', 'sis_section_id', 'section_id', 'role', 'status']
        #
        for row in searchResults:
            course_id = row['course_id']
            courseStatus = canvasCourseInfo(row['course_id'], canvasApi, authHeader)
            if len(courseStatus) > 1:
                tableTemp.append([row['course_id'], str(row['id']), row['sis_user_id'], row['sis_course_id'], row["sis_section_id"], int(row["course_section_id"]), row['role'], row['enrollment_state']])
                canvasEnrollIDs.append(str(row['id']))
            else: continue
        table = columnar(tableTemp, columnHeaders, no_borders=True)
        #
        print(table)
        while enrollRestoreSelection not in canvasEnrollIDs and enrollRestoreSelection != 'AC':
            print()
            enrollRestoreSelection = str(input("Enrollment ID to review (q to quit, AC for 'all-completed'): "))
            if enrollRestoreSelection == 'q': break
            else: continue
        print()
        if enrollRestoreSelection == 'AC':            # LOOP FOR UPDATING NON-ACTIVE ENROLLMENTS TO COMPLETED
            print()
            input("> Press <enter> to continue resetting all non-active enrollments to 'completed'...")
            print()
            for row in tableTemp:
                if row[7] == 'active': continue
                else:
                    enrollmentNewStatus = 'completed'
                    print(f'=== Updating: {row}')
                    print()
                    print(f'  = Student Access Report: {canvasUrl}/courses/{row[0]}/users/{canvasUserID}/usage')
                    print()
                    canvasEnrollmentEdit(canvasApi, authHeader, row, enrollmentNewStatus)
                    print()
                    time.sleep(sleepDelay)
        elif enrollRestoreSelection != 'q':           # SINGLE ENROLLMENT CHANGE FOR ANY ENROLLMENT TYPE
            for row in tableTemp:
                if row[1] == enrollRestoreSelection:
                    enrollInfoUrl = f'{canvasApi}accounts/{canvasAccountID}/enrollments/{enrollRestoreSelection}'
                    enrollInfo = requests.get(enrollInfoUrl,headers=authHeader).json()
                    enrollInfo = canvasJsonDates(enrollInfo)
                    print()
                    print('>>> Enrollment details:')
                    print()
                    print(f'    Enroll ID:       {enrollRestoreSelection}')
                    print(f'    Enroll State:    {enrollInfo["enrollment_state"]}')
                    print(f'    NetID:           {enrollInfo["sis_user_id"]}')
                    print(f'    Course ID:       {enrollInfo["sis_course_id"]}')
                    print(f'    Section ID:      {enrollInfo["sis_section_id"]}')
                    print(f'    Course Role:     {enrollInfo["role"]}')
                    print(f'    Sub-account:     {enrollInfo["sis_account_id"]}')
                    print(f'    Created:         {enrollInfo["created_at"]}')
                    if "last_activity_at" not in enrollInfo:
                        print(f'    Last Activity:   n/a')
                    else:
                        print(f'    Last Activity:   {enrollInfo["last_activity_at"]}')
                    if "total_activity_time" not in enrollInfo:
                        print(f'    Total Activity:  n/a')
                    else:
                        print(f'    Total Activity:  {enrollInfo["total_activity_time"]} minutes')
                    print()
                    print('    Links for this enrollment which must be "completed" or "active" to use:')
                    print()
                    print(f'    - Access Report: {enrollInfo["html_url"]}/usage')
                    print(f'    - Grades Report: {canvasUrl}/courses/{enrollInfo["course_id"]}/grades/{enrollInfo["user_id"]}')
                    print()
                    break
            while enrollmentNewStatus != 'q' and enrollmentNewStatus != 'a' and enrollmentNewStatus != 'c' and enrollmentNewStatus != 'd' and enrollRestoreSelection != 'q':
                print('')
                enrollmentNewStatus = input("> Enter new status or (q)uit:  (a)ctive, (c)ompleted, (d)eleted: ").lower()
                print('')
            if enrollmentNewStatus == 'a': enrollmentNewStatus = 'active'
            elif enrollmentNewStatus == 'c': enrollmentNewStatus = 'completed' # DEBUG
            elif enrollmentNewStatus == 'd': enrollmentNewStatus = 'deleted'
            else: enrollmentNewStatus == 'q'
            print('')
            if enrollRestoreSelection != 'q' and enrollmentNewStatus != 'q' and enrollRestoreSelection in canvasEnrollIDs and enrollmentNewStatus != row[7]:
                enrollConfirm = yesOrNo(f"Modify this enrollment from {row[7].upper()} to {enrollmentNewStatus.upper()}  status?  {enrollRestoreSelection}")
                if enrollConfirm == True:
                    for row in tableTemp:
                        if row[1] == enrollRestoreSelection:
                            canvasEnrollmentEdit(canvasApi, authHeader, row, enrollmentNewStatus)
            else:
                print("Closing connection. No changes made.")
            print('')
        else:
            print("Closing connection. No changes made.")
            print('')
    else:
        print(f"No {status} courses found for user {netID} in term {tempTermID}.")
        print('')
    while answer != 'y' and answer != 'n':
        answer = input(f"Continue with another enrollment on {envLabel} (y/n)? ").strip().lower()
    if answer == 'y':
        print()
        continue
    else:
        print()
        break
#
print("Closing connection and exiting...")
print('')
