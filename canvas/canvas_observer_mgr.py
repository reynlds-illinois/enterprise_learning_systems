import os, sys
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
envDict = getEnv()
import requests
from requests_toolbelt import sessions
import csv
from pprint import pprint
action = ''
env = ''
logScriptStart()
#
print('')
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower().strip()
    if env == 'p':
        canvasApi = envDict["canvas.api-prod"]
        canvasToken = envDict["canvas.write-token"]
        envLabel = "PROD"
    else:
        canvasApi = envDict["canvas.api-beta"]
        canvasToken = envDict["canvas.write-token"]
        envLabel = "STAGE"
print("Connected to:", canvasApi)
print('')
#
s = sessions.BaseUrlSession(base_url=canvasApi)
s.headers['Authorization'] = f"Bearer {canvasToken}"
#
def canvasListObservees():
    print('')
    observer = input("Enter the NetID of the Advising Observer: ")
    observerID = canvasGetUserInfo(observer)[0]
    #print(f"observerID: {observerID}")
    try:
        r = s.get(f'users/{observerID}/observees').json()
        return(r)
    except:
        #print("FAILED")
        return('False')
def canvasListObservers():
    print('')
    studentObservee = input("Enter the NetID of the Student Observee:  ")
    observeeID = canvasGetUserInfo(studentObservee)[0]
    #print(f"observeeID: {observeeID}")
    try:
        r = s.get(f'users/{observeeID}/observers').json()
        return(r)
    except:
        #print("FAILED")
        return('False')
def canvasAddObserver():
    print('')
    studentObservee = input("Enter the NetID of the Student Observee:  ")
    observer = input("Enter the NetID of the Observer: ")
    observeeID = canvasGetUserInfo(studentObservee)[0]
    observerID = canvasGetUserInfo(observer)[0]
    try:
        r = s.put(f'users/{observerID}/observees/{observeeID}').json()
        return(r.text)
    except:
        return('False')
def canvasBulkAddObservers():
    print('')
    rdict = []
    feederFile = input("Enter filename for file in this location, /var/lib/canvas-mgmt/tmp : ")
    with open(feederFile, 'r') as csvFile:
        #obReader = csv.reader(csvFile, delimiter=',')
        next(obReader, None)  # skip the headers
        for row in obReader:
            try:
                observerID = canvasGetUserInfo(row[0])[0]
                observeeID = canvasGetUserInfo(row[1])[0]
                r = s.put(f'users/{observerID}/observees/{observeeID}')
                print(f"Successfully added {row[0].upper()} as an observer for {row[1].upper()}")
            except:
                print(f"Encountered an issue when adding {observer.upper()} as an observer {observee.upper()}")
def canvasDelObserver():
    print('')
    obNetID = input("Enter NetID of Observer: ")
    stNetID = input("Enter NetID of Student Observee: ")
    observerID = canvasGetUserInfo(obNetID)[0]
    observeeID = canvasGetUserInfo(stNetID)[0]
    r = s.delete(f'users/{observerID}/observees/{observeeID}')
    if r.status_code == 200:
        return(r.text)
    else:
        return('False')
#
print('')
while action != 'l' and action != 'c' and action != 'd' and action != 's' and action != 'q' and action != 'b':
    print("Do you want to:  (L)ist observers assigned to a student? ")
    print("                 (S)how students assigned to an Observer?")
    print("                 (C)reate an observer realationship for a student?")
    print("                 (D)elete an observer/student relationship?")
    print("                 (B)ulk add observer/student relationships with feeder file?")
    print("                 (Q)uit without changes?")
    print('')
    action = input("                > ").lower()[0]
if action == 'l':
    x = canvasListObservers()
    if len(x) > 0:
        print("| This account is being observed by the following advisors:")
        for row in x:
            print(f"|    {row['sis_user_id']} - {row['name']}")
    else:
        print("> That account has no advisors observing.")
    print('')
elif action == 's':
    print('')
    x = canvasListObservees()
    if len(x) > 0:
        print("| This account is observing the following students:")
        for row in x:
            print(f"|    {row['sis_user_id']} - {row['name']}")
    else:
        print('')
        print("> That account has no students under observation.")
    #pprint(x)
    print('')
elif action == 'c':
    x = canvasAddObserver()
elif action == 'd':
    x = canvasDelObserver()
    if x == 'False':
        print('')
        print("| There was an issue retrieving the association requested. Please check")
        print("| the data used and confirm the relationship exists in Canvas.")
        print('')
    else:
        print('')
        print("| Observer relationship successfully removed from Canvas.")
        #pprint(x)
        print('')
elif action == 'b':
    x = canvasBulkAddObservers()
else:
    print('')
    print("> Exiting without changes...")
    print('')
    s.close()
