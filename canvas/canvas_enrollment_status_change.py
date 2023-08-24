######################################################################
# This script allows changes to a Canvas enrollment in real-time.
# It was originally used to restore enrollments that had been deleted or completed.
######################################################################
#!/usr/bin/python
import sys, os, json, csv, requests, datetime
from columnar import columnar
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
from pprint import pprint
envDict = getEnv()
env = 'x'
print('')
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower()[0]
    if env == 'p':
        canvasApi = envDict["canvas.api-prod"]
        print('')
        print("> Connected to Canvas PRODUCTION")
        print('')
    else:
        canvasApi = envDict["canvas.api-beta"]
        print('')
        print("> Connected to Canvas BETA/STAGE")
        print('')
print('')
canvasReadToken = envDict["canvas.ro-token"]
canvasWriteToken = envDict["canvas.write-token"]
readHeaders = {"Authorization": f"Bearer {canvasReadToken}"}
writeHeaders = {"Authorization": f"Bearer {canvasWriteToken}"}
canvasAccountId = "1"
canvasUserID = 'F'
searchResults = []
enrollRestoreSelection = ''
enrollmentNewStatus = 'x'
status = 'x'
canvasEnrollIDs = []
canvasSectionID = ''
while canvasUserID == "F":
    netID = input("Enter the NetID of the user: ")
    canvasUserID = canvasGetUserInfo(netID)[0]
    if canvasUserID != "F":
        continue
    else:
        print("That user is not found. Please try again.")
print('')
termID = input("Banner Term Code (leave blank for 'all'): ")
if not termID:
    enrollmentsUrl = f"{canvasApi}users/{canvasUserID}/enrollments"
    tempTermID = 'ALL'
else:
    enrollmentsUrl = f"{canvasApi}users/{canvasUserID}/enrollments?enrollment_term_id=sis_term_id%3A{termID}"
    tempTermID = termID
print('')
while status != 'a' and status != 'i' and status != 'd' and status != 'c' and status != '':
    status = input("Enter enrollment status:  (a)ctive, (c)ompleted, (d)eleted, (i)nactive, <enter> for all:  ")
    print('')
if status == "a":
    status = ["active"]
elif status == "c":
    status = ["completed"]
elif status == "d":
    status = ["deleted"]
elif status == "i":
    status = ["inactive"]
else:
    status = ["active", "inactive", "deleted", "completed"]
print("")
for item in status:
    params = {"per_page": 100, "state":f"{item}"}
    response = requests.get(enrollmentsUrl, headers=readHeaders, params=params)
    if len(response.json()) > 0:
        searchResults.extend(response.json())
        while 'next' in response.links:
            response = requests.get(response.links['next']['url'], readHeaders=headers, params=params)
            searchResults.extend(response.json())
if len(searchResults) > 0:
    tableTemp = []
    columnHeaders = ['canvas_id', '>ENROLL_ID<', 'net_id', 'course_id', 'section_id', 'c_section_id', 'role', 'status']
    for row in searchResults:
        tableTemp.append([row['course_id'], str(row['id']), row['sis_user_id'], row['sis_course_id'], row["sis_section_id"], int(row["course_section_id"]), row['role'], row['enrollment_state']])
        canvasEnrollIDs.append(str(row['id']))
    table = columnar(tableTemp, columnHeaders, no_borders=True)
    print(table)
    while enrollRestoreSelection not in canvasEnrollIDs and enrollRestoreSelection != 'q':
        enrollRestoreSelection = input("Enrollment ID to change (q/Q to stop):  ").lower()
        for row in tableTemp:
            if row[1] == enrollRestoreSelection:
                print('')
                print(f'  Enrollment ID:  {row[1]}')
                print(f'  NetID:          {row[2]}')
                print(f'  Course ID:      {row[3]}')
                print(f'  Section ID:     {row[4]}')
                print(f'  Course Role:    {row[6].replace("Enrollment","")}')
                print(f'  Current Status: {row[7]}')
                break
        while enrollmentNewStatus != 'a' and enrollmentNewStatus != 'c' and enrollmentNewStatus != 'd' and enrollRestoreSelection != 'q':
            print('')
            enrollmentNewStatus = input("Enter new status:  (a)ctive, (c)ompleted, (d)eleted:  ").lower()
            print('')
        if enrollmentNewStatus == 'a':
            enrollmentNewStatus = 'active'
        elif enrollmentNewStatus == 'c':
            enrollmentNewStatus = 'completed'
        else:
            enrollmentNewStatus = 'deleted'
    print('')
    if enrollRestoreSelection != 'q' and enrollRestoreSelection in canvasEnrollIDs and enrollmentNewStatus != row[7]:
        enrollConfirm = yesOrNo(f"Restore this enrollment from {row[7].upper()} to {enrollmentNewStatus.upper()}  status?  {enrollRestoreSelection}")
        if enrollConfirm == True:
            for row in tableTemp:
                if row[1] == enrollRestoreSelection:
                    params = {"enrollment[user_id]":canvasUserID,
                              "enrollment[type]":row[6],
                              "enrollment[enrollment_state]":enrollmentNewStatus,
                              "enrollment[notify]":False,
                              "enrollment[course_section_id]":row[5],
                              }
                    url = f"{canvasApi}courses/{row[0]}/enrollments"
                    enrollRestore = requests.post(url, headers=writeHeaders, params=params)
                    print('')
                    print(enrollRestore.reason)
                    print(enrollRestore.text)
                    print('')
        else:
            print("Closing connection. No changes made.")
        print('')
    else:
        print("Closing connection. No changes made.")
        print('')
else:
    print(f"No {status} courses found for user {netID} in term {tempTermID}.")
    print('')
