#!/usr/bin/python
#
import sys, os
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm, logScriptStart, getEnv, canvasGetUserInfoLive
#logScriptStart()
realm = realm()
env = getEnv()
canvasAPI = realm['canvasApi']
canvasToken = realm['canvasToken']
answer = ''
#params = {"per_page": 100}
canvasAuth = {"Authorization": f"Bearer {canvasToken}"}
print()
while answer != 'y' and answer != 'n':
    searchTerm = input("Enter NetID, UIN or Canvas ID to search:  ").lower()
    print()
    canvasGetUserInfoLive(searchTerm, canvasAPI, canvasAuth)
    answer = input("Continue with another search (y/n)? ").strip().lower()
    if answer == 'y':
        print()
        answer = ''
        continue
    else:
        print()
        break
print(f'Exiting and closing connection to {canvasAPI}')
print()