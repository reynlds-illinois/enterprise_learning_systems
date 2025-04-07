#!/usr/bin/python
#
import sys, requests, json
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
netID = input('Please enter the NetID: ')
canvasUserID = canvasGetUserInfo(netID)[0]
print()
groupID = input('Please enter the target group ID from the course: ')
print()
try:
    params = {'user_id':canvasUserID}
    r = requests.post(f"{canvasApi}groups/{groupID}/memberships", headers=authHeader, params=params)
    print(f"{r.reason} - User {netID} - {canvasUserID} has been added to group {groupID}.")
    print()
except Exception as E:
    print(E)
    print()
