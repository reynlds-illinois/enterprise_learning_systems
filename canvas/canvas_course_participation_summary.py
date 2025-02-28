#!/usr/bin/python
#
import sys, os, json, requests
from columnar import columnar
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from pprint import pprint
realm = realm()
canvasAPI = realm['canvasApi']
canvasAuth = {"Authorization": f"Bearer {realm['canvasToken']}"}
canvasEnv = realm['envLabel']
sortMethod = ''
#
def canvasCourseStudentSummary(canvasCourseID, canvasAPI, canvasAuth):
    """Return per-user access info for all users in a course"""
    searchResults = []
    params = {"per_page":100}
    url = f"{canvasAPI}courses/{canvasCourseID}/analytics/student_summaries"
    response = requests.get(url, headers=canvasAuth, params=params)
    searchResults = response.json()
    while 'next' in response.links:
        response = requests.get(response.links['next']['url'], headers=canvasAuth, params=params)
        searchResults.extend(response.json())
    if len(searchResults) < 1:
        print("No Stat Summaries Found")
        print()
    else:
        print()
        return searchResults
#
def canvasUserIDInfo(canvasUserID, canvasAPI, canvasAuth):
    """Return Canvas user info when Canvas user ID is provided"""
    url = f"{canvasAPI}users/{canvasUserID}"
    response = requests.get(url, headers=canvasAuth).json()
    if len(response) < 1:
        print()
        print(f"User Not Found: {canvasUserID}")
        print()
    else:
        return response
#
def canvasCourseInfo(uiucCourseID, canvasAPI, canvasAuth):
    """Return Canvas course info when UIUC course ID is provided"""
    searchResults = []
    url = f"{canvasAPI}accounts/1/courses/?search_term={uiucCourseID}"
    response = requests.get(url, headers=canvasAuth)
    searchResults = response.json()
    if len(searchResults) < 1:
        print()
        print(f"Course Not Found: {uiucCourseID}")
        print()
    else:
        return searchResults[0]
#
columnHeader = ['NETID', 'PAGE_VIEWS', 'PAGE_VIEWS_LEVEL', 'PARTICIPATIONS', 'PARTICIPATIONS_LEVEL', 'TARDINESS_BREAKDOWN']
finalData = []
uiucCourseID = input("Enter the UIUC Course ID: ")
print()
while sortMethod != 'u' and sortMethod != 'p':
    sortMethod = input("Sort by (u)ser or (p)articipation level: ").lower().split()[0]
    print()
canvasCourseID = canvasCourseInfo(uiucCourseID, canvasAPI, canvasAuth)['id']
pageViewSummary = canvasCourseStudentSummary(canvasCourseID, canvasAPI, canvasAuth)
#
for item in pageViewSummary:
    uiucNetID = canvasUserIDInfo(item['id'], canvasAPI, canvasAuth)['sis_user_id']
    if uiucNetID is None:
        continue
    else:
        finalData.append([str(uiucNetID), item['page_views'], item['page_views_level'], item['participations'], item['participations_level'], item['tardiness_breakdown']])
if sortMethod == 'u':
    finalData.sort(key=lambda x: x[0])
else:
    finalData.sort(key=lambda x: (x[1]), reverse=True)
table = columnar(finalData, columnHeader, no_borders=True)
print(f'=== Summary for {uiucCourseID} ===')
print()
print(table)
print()
