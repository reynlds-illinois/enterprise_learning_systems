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
canvasReadToken = env["canvas.ro-api"]
canvasWriteToken = env["canvas.write-token"]
readHeaders = {"Authorization": f"Bearer {canvasReadToken}"}
writeHeaders = {"Authorization": f"Bearer {canvasWriteToken}"}
canvasAccountId = "1"
canvasUserID = 'F'
searchResults = []
enrollRestoreSelection = ''
status = ["inactive", "deleted", "completed"]
canvasEnrollIDs = []
canvasSectionID = ''
print('')
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
    columnHeaders = ['canvas_id', '>enroll_id<', 'net_id', 'course_id', 'section_id', 'c_section_id', 'role', 'status']
    for row in searchResults:
        tableTemp.append([row['course_id'], str(row['id']), row['sis_user_id'], row['sis_course_id'], row["sis_section_id"], int(row["course_section_id"]), row['role'], row['enrollment_state']])
        canvasEnrollIDs.append(str(row['id']))
    table = columnar(tableTemp, columnHeaders, no_borders=True)
    print(table)
    while enrollRestoreSelection not in canvasEnrollIDs and enrollRestoreSelection != 'q':
        enrollRestoreSelection = input("Enrollment ID to restore (q/Q to stop):  ").lower()
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
    print('')
    if enrollRestoreSelection != 'q' and enrollRestoreSelection in canvasEnrollIDs:
        enrollConfirm = yesOrNo(f"Restore this enrollment ID?  {enrollRestoreSelection}")
        if enrollConfirm == True:
            for row in tableTemp:
                if row[1] == enrollRestoreSelection:
                    params = {"enrollment[user_id]":canvasUserID,
                              "enrollment[type]":row[6],
                              "enrollment[enrollment_state]":"active",
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
    print(f"No deleted enrollments found for user {netID} in term {tempTermID}.")
    print('')

