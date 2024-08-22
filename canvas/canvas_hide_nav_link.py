#!/usr/bin/python
#
import sys, os, json, requests
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
realm = realm()
canvasAPI = realm['canvasApi']
canvasAuth = {"Authorization": f"Bearer {realm['canvasToken']}"}
canvasEnv = realm['envLabel']
yesNo = ''
#
def canvasHideLink(canvasCourseID, canvasLinkID, canvasAPI, canvasAuth):
    params = {"hidden":True}
    url = f"{canvasAPI}courses/{canvasCourseID}/tabs/{canvasLinkID}"
    r = requests.put(url, headers=canvasAuth, params=params).json()
    return r
#
print()
navigationLabel = input("Enter nav label to search for or press <enter> to use the default (Day1Access Course Materials).")
print()
# will add CD2 SQL lookup here at some point...for now it's a manual input
courseListing = input("Enter your list of Canvas course IDs (one line, space separated):  ")
courseListing = list(courseListing.split(" "))
courses = len(courseList)
#
while yesNo != 'y' and yesNo != 'n':
    yesNo = input(f"Continue changing the {navigationLabel} for {courses} Canvas courses (y/n)? ").lower()[0]
    print()
if yesNo = 'y':
    for courseID in courseListing:
        try:
            print(now())
            courseTabs = requests.get(f"{canvasAPI}courses/{courseID}/tabs", headers=canvasAuth).json()
            for item in courseTabs:
                if item['label'] == 'Day1Access Course Materials':
                    canvasLinkID = item['id']
                    courseUpdate = canvasHideLink(courseID, canvasLinkID, canvasAPI, canvasAuth)
            print(f"> Course ID {courseID} with Link ID {canvasLinkID} has been successfully updated.")
            #print()
        except Exception as e:
            print(f"### Course ID {courseID} Error:  {e}")
            #print()
else:
    print()
    print("Exiting...no changes made...")
    print()
