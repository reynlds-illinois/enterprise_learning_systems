#!/usr/bin/python
#
import sys, os, json, csv, requests, datetime
from columnar import columnar
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
from pprint import pprint
env = getEnv()
logScriptStart()
canvasApi = env["canvas.api-prod"]
canvasToken = env["canvas.ro-api"]
headers = {"Authorization": f"Bearer {canvasToken}"}
canvasAccountId = "1"
status = '0'
role = '0'
userID = 'F'
searchResults = []
#
print("")
while userID == "F":
    netID = input("Enter the NetID of the user: ")
    userID = canvasGetUserInfo(netID)[0]
    if userID != "F":
        continue
    else:
        print("That user is not found. Please try again.")
#
print("Canvas User ID Found:", userID)
while status !='' and status !='active' and status !='inactive' and status != 'invited' and status != 'completed' and status != 'deleted' and status != 'rejected':
    print('|----------------------------------------------------')
    print("| Enrollment status:")
    print("|    - active")
    print("|    - inactive")
    print("|    - invited")
    print("|    - completed")
    print("|    - deleted")
    print("|    - rejected")
    print('|----------------------------------------------------')
    status = input("|      <enter> for ALL: ")
    print('|----------------------------------------------------')
if status == '':
    status = ["active", "invited", "rejected", "deleted", "completed", "rejected"]
else:
    status = [status]
print('')
#
while role != '' and role !='teacher' and role !='student' and role!='ta' and role !='designer' and role !='grader':
    print('|----------------------------------------------------')
    print("| Available roles:")
    print("|    - teacher")
    print("|    - student")
    print("|    - ta")
    print("|    - designer")
    print("|    - grader")
    print('|----------------------------------------------------')
    role = input("|      <enter> for ALL: ")
    print('|----------------------------------------------------')
print('')
#
print('|----------------------------------------------------')
termID = input("| Banner Term Code (leave blank for 'all'): ")
print('|----------------------------------------------------')
print('')
#
if not termID:
    enrollmentsUrl = f"{canvasApi}users/{userID}/enrollments"
else:
    enrollmentsUrl = f"{canvasApi}users/{userID}/enrollments?enrollment_term_id=sis_term_id%3A{termID}"
#
print("One moment please...")
for item in status:
    params = {"per_page": 100, "state":f"{item}"}
    response = requests.get(enrollmentsUrl, headers=headers, params=params)
    if len(response.json()) > 0:
        searchResults.extend(response.json())
        while 'next' in response.links:
            response = requests.get(response.links['next']['url'], headers=headers, params=params)
            searchResults.extend(response.json())
#
print('')
if len(searchResults) > 0:
    tableTemp = []
    columnHeaders = ['canvas_id', 'enroll_id', 'net_id', 'course_id', 'section_id', 'role', 'enrollment_state', 'created']
    for row in searchResults:
        tableTemp.append([row['course_id'], row['id'], row['sis_user_id'], row['sis_course_id'], row["sis_section_id"], row['role'].replace('Enrollment',''), row['enrollment_state'], row['created_at']])
    if len(role) == 0 and len(status) == 6:                   # all roles, all statuses
        results2 = tableTemp
    elif len(role) > 0 and len(status) == 6:                  # role provided, but no status
        results2 = []
        for row in tableTemp:
            if str(row[5]).lower() == role:
                results2.append(row)
    elif len(role) == 0 and len(status[0]) != 0:              # no role, but status provided
        results2 = []
        for row in tableTemp:
            if str(row[6]).lower() == status[0]:
                results2.append(row)
    else:                                                     # both role and status provided
        results2 = []
        for row in tableTemp:
            if str(row[5]).lower() == role and str(row[6]) == status[0]:
                results2.append(row)
    table = columnar(results2, columnHeaders, no_borders=True)
    print(table)
    print('|----------------------------------------------------')
    reply = str(input('| Export to CSV (y/n): ')).lower().strip()
    if reply[:1] == 'y':
        now = datetime.datetime.now().timestamp()
        targetFile = f'/var/lib/canvas-mgmt/reports/enrollments_{netID}_{now}.csv'
        with open (targetFile, 'w') as exportFile:
            write = csv.writer(exportFile, delimiter='|')
            write.writerow(columnHeaders)
            write.writerows(results2)
        print(f'| CSV Export file: {targetFile}')
        print('|----------------------------------------------------')
    else:
        print('| Complete')
        print('|----------------------------------------------------')
else:
    print(f"No {status[0]} enrollments found for {netID}")
print('')
