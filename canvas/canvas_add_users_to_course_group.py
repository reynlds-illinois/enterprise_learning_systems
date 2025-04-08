#!/usr/bin/python
#
import sys, requests, getpass, json, csv
#from columnar import columnar
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import canvasGetUserInfo
#env = getEnv()
#logScriptStart()
realm = realm()
print()
canvasApi = realm["canvasApi"]
#canvasToken = realm["canvasToken"]
adminToken = getpass.getpass('Enter your SU token: ')
authHeader = {"Authorization": f"Bearer {adminToken}"}
#netID = input('Please enter the NetID: ')
#groupID = input('Please enter the target group ID from the course: ')
print()
sourceFile = input('Please enter the full file path to the CSV source file: ')
print()
with open(sourceFile, 'r') as csvFile:
    reader = csv.reader(csvFile, delimiter=',')
    for row in reader:
        netID = row[0]
        groupID = row[1]
        canvasUserID = canvasGetUserInfo(netID)[0]
        params = {'user_id':canvasUserID}
        r = requests.post(f"{canvasApi}groups/{groupID}/memberships", headers=authHeader, params=params)
        pprint(r)
        print('----------')
        print()
        input('Press <ENTER> to continue...')
        print()