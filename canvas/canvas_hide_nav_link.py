#!/usr/bin/python
#
import sys, os, json, requests
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import now
realm = realm()
canvasAPI = realm['canvasApi']
canvasAuth = {"Authorization": f"Bearer {realm['canvasToken']}"}
canvasEnv = realm['envLabel']
navigationLabel = ''
yesNo = ''
#
def canvasHideLink(canvasCourseID, canvasLinkID, canvasAPI, canvasAuth):
    params = {"hidden":True}
    url = f"{canvasAPI}courses/{canvasCourseID}/tabs/{canvasLinkID}"
    r = requests.put(url, headers=canvasAuth, params=params).json()
    return r
#
print()
navigationLabel = input(">>> Enter nav label to search for (note: this is case-dependent): ")
print()
#
myChoice = ''
while myChoice != 'e' and myChoice != 'f' and myChoice != 'q':
    myChoice = input("### Enter 'e' to enter course IDs manually, 'f' to read from a file, or 'q' to quit: ").lower()[0]
    print()
#
if myChoice == 'e':
    courseListing = input(">>> Enter your list of Canvas course IDs (one line, space separated):  ")
    courseListing = list(courseListing.split(" "))
    courses = len(courseListing)
    #
    while yesNo != 'y' and yesNo != 'n':
        yesNo = input(f">>> Continue changing the {navigationLabel} for {courses} Canvas courses (y/n)? ").lower()[0]
        print()
    if yesNo == 'y':
        for courseID in courseListing:
            try:
                #print(now())
                courseTabs = requests.get(f"{canvasAPI}courses/{courseID}/tabs", headers=canvasAuth).json()
                for item in courseTabs:
                    if item['label'] == navigationLabel:
                        canvasLinkID = item['id']
                        courseUpdate = canvasHideLink(courseID, canvasLinkID, canvasAPI, canvasAuth)
                print(f"> Course ID {courseID} with Link ID {canvasLinkID} has been successfully updated.")
                print()
            except Exception as e:
                print(f"### Course ID {courseID} Error:  {e}")
                #print()
#
if myChoice == 'f':
    yesNo = ''
    fileName = input("### Enter the file name (with path if needed): ")
    try:
        with open(fileName, 'r') as f:
            courseListing = f.read().splitlines()
            courses = len(courseListing)
            #print(f">>> {courses} course IDs read from file {fileName}.")
            print()
            while yesNo != 'y' and yesNo != 'n':
                yesNo = input(f">>> Continue changing the {navigationLabel} for {courses} Canvas courses (y/n)? ").lower()[0]
                print()
            if yesNo == 'y':
                for courseID in courseListing:
                    try:
                        #print(now())
                        courseTabs = requests.get(f"{canvasAPI}courses/{courseID}/tabs", headers=canvasAuth).json()
                        for item in courseTabs:
                            if item['label'] == navigationLabel:
                                canvasLinkID = item['id']
                                courseUpdate = canvasHideLink(courseID, canvasLinkID, canvasAPI, canvasAuth)
                        print(f"> Course ID {courseID} with Link ID {canvasLinkID} has been successfully updated.")
                        print()
                        #print()
                    except Exception as e:
                        print(f"### Course ID {courseID} Error:  {e}")
            else:
                print("Exiting...no changes made...")
                print()
                sys.exit()
    except Exception as e:
        print(f"### Error reading file {fileName}:  {e}")
        print("Exiting...")
        print()
        sys.exit()
elif myChoice == 'q':
    print("Exiting...no changes made...")
    print()
    sys.exit()
