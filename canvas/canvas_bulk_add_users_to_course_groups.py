# requires a CSV file formatted as "netID,groupID" with no header
# Example:  jdoe,123456789
#           janed,111111111
#           johnd,222222222
#
#!/usr/bin/python
#
import sys, requests, getpass, json, csv
from columnar import columnar
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
columnHeaders = ['Status Code', 'NetID', 'Group ID']
print()
sourceFile = input('Please enter the FULL file path to the CSV file: ')
print()
with open(sourceFile, 'r') as csvFile:
    reader = csv.reader(csvFile, delimiter=',')
    groupAdds = []
    groupFails = []
    for row in reader:
        netID = row[0]
        groupID = row[1]
        print(f'Adding {netID} to group {groupID}')
        canvasUserID = canvasGetUserInfo(netID)[0]
        params = {'user_id':canvasUserID}
        r = requests.post(f"{canvasApi}groups/{groupID}/memberships", headers=authHeader, params=params)
        #pprint(r)
        if r.status_code == 200:
            print(f'User {netID} added to group {groupID}')
            groupAdds.append([r.status_code, netID, groupID])
        elif r.status_code == 404:
            print(f'User {netID} not found.')
            groupFails.append([r.status_code, netID, groupID])
        elif r.status_code == 403:
            print(f'Permission denied for user {netID}.')
            groupFails.append([r.status_code, netID, groupID])
        elif r.status_code == 422:
            print(f'User {netID} already in group {groupID}.')
            groupFails.append([r.status_code, netID, groupID])
        elif r.status_code == 401:
            print(f'Authentication failed for user {netID}.')
            groupFails.append([r.status_code, netID, groupID])
        elif r.status_code == 500:
            print(f'Internal server error for user {netID}.')
            groupFails.append([r.status_code, netID, groupID])
        elif r.status_code == 503:
            print(f'Service unavailable for user {netID}.')
            groupFails.append([r.status_code, netID, groupID]) 
        else:
            print(f'Error: {r.status_code} - {r.text}')
        print('----------')
        print()
print('===== SUMMARY =====')
print(f'| Successful group updates:  {len(groupAdds)}')
print(f'| Failed group updates:      {len(groupFails)}')
print('====================')
print()
if len(groupFails) > 0:
    print('===== FAILED GROUP UPDATES =====')
    print(columnar(groupFails, columnHeaders, no_borders=True))
    print('==============================')
    print()
