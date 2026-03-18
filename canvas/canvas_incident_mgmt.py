#!/usr/bin/python
#
import sys, os, requests, json
from time import timezone
from datetime import datetime, UTC
from pprint import pprint
from columnar import columnar
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
#
realm = realm()
apiKey = realm['shKey']
serviceID = realm['shServiceID']
acctSubdomain = realm['shAcctSubdomain']
subDomain = realm['shSubdomain']
baseURL = f'https://{acctSubdomain}.app.statushub.io/api/v3/hubs'
timeFormat = '%Y-%m-%d %h:%m:%s'
payload = {}
#headers = {'Content-Type': 'application/json', 'Accept': 'application/vnd.statushub.v2'}
requestHeaders = {'Content-Type': 'application/json', 'X-API-KEY': apiKey}
query = {'api_version': 'V3-R1'}
myChoice = ''
params = {}
again = ''
columnHeader = ['id', 'service', 'service_state', 'title', 'created', 'last_update', 'incident_status']
openIncidentsHeader = ['id','end_date','start_date','status','incident_title']
incidentTypes = {'i': 'investigating', 'r': 'resolved', 'n': 'identified', 'm': 'monitoring'}
serviceStatusTypes = {'dp': 'degraded-performance', 'u': 'up', 'd': 'down'}
#
def resolveIncident(baseURL, subDomain, requestHeaders, incident):
    query = {'api_version': 'V3-R1'}
    url = f"{baseURL}/{subDomain}/incidents/{incident[0]}/incident_updates"
    #print(f'> url: {url}')
    nowUTC = datetime.now(UTC)
    endDateStamp = nowUTC.strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "title": incident[4],
        "start_time": endDateStamp,
        "incident_type": "resolved",
        "body": "This incident has been resolved.",
        "silent": False,
        "state": "published"
    }
    #print(f'payload: {payload}')
    response = requests.post(url, json=payload, headers=requestHeaders, params=query)
    if response.status_code == 200:
        print('  = Incident resolved successfully.')
        print()
    else:
        print('  = Something went wrong. Please try again.')
        print(f'  >>> ERROR:  {response.text}')
        print()
#
def updateIncident(baseURL, subDomain, requestHeaders, query, incidentTypes, serviceStatusTypes):
    query = {'api_version': 'V3-R1'}
    yesNo = ''
    incidentTypeInput = ''
    serviceStatusInput = ''
    print()
    incidentID = input('  = Please provide the ID of the Incident:  ')
    print()
    while incidentTypeInput not in incidentTypes:
        incidentTypeInput = input("  = Update type: (i)nvestigating, (r)esolved, ide(n)tified, (m)onitoring > ")
        print()
    incidentType = str(incidentTypes.get(incidentTypeInput))
    while serviceStatusInput not in serviceStatusTypes:
        serviceStatusInput = input("  = Current service status: (dp)egraded performance, (u)p, (d)own ")
        print()
    serviceStatus = str(serviceStatusTypes.get(serviceStatusInput))
    url = f"{baseURL}/{subDomain}/incidents/{incidentID}/incident_updates"
    print()
    incidentTitle = input('  = Please provide a short title for this update:  ')
    print()
    incidentBody = input('  = Please provide a description of this update:  ')
    print()
    nowUTC = datetime.now(UTC)
    updateDateStamp = nowUTC.strftime("%Y-%m-%dT%H:%M:%SZ")
    while yesNo not in ['y','n']:
        yesNo = input(f'  = Continue updating Incident # {incidentID} (y/n)? ').strip().lower()
        print()
    if yesNo == 'y':
        print(f'  = Updating Incident # {incidentID} with the following information:')
        print()
        print(f'    - Title: {incidentTitle}')
        print(f'    - Type: {incidentType}')
        print(f'    - Description: {incidentBody}')
        print(f'    - Start Time: {updateDateStamp}')
        print(f'    - Service Status: {serviceStatus}')
        print()
        payload = {
            "title": incidentTitle,
            "incident_type": incidentType,
            "body": incidentBody,
            "start_time": updateDateStamp,
            "service_statuses": [
                {
                    "service_id": serviceID,
                    "status": serviceStatus
                }
            ]
        }
        response = requests.post(url, headers=requestHeaders, params=query, json=payload)
        if response.status_code == 200:
            print('  = Incident updated successfully.')
        else:
            print('  = Something went wrong. Please try again.')
            print(f'  = ERROR:  {response.text}')
        print()
    else:
        print('  = Incident resolution cancelled.')
        print()
#
def getIncident(baseURL, subDomain, requestHeaders, incidentID):
    #requestHeaders = {'X-API-KEY': apiKey}
    query = {'api_version': 'V3-R1'}
    url = f"{baseURL}/{subDomain}/incidents/{incidentID}"
    response = requests.get(url, headers=requestHeaders, params=query)
    if response.status_code == 200:
        tempJson = json.loads(response.text)
    if len(tempJson) > 0:
        print()
        print(f'  = ID:           {tempJson["id"]}')
        print(f'  = Author:       {tempJson["author"]}')
        print(f'  = Title:        {tempJson["title"]}')
        print(f'  = Start Time:   {tempJson["start_time"]}')
        print(f'  = Last Update:  {tempJson["updated_at"]}')
        print(f'  = End Time:     {tempJson["end_time"]}')
        #print(f'  = Status:       {tempJson["last_incident_type"]}')
        print()
            #print(tempJson)
        return tempJson
#
def getOpenIncidents(baseURL, subDomain, apiKey, query):
    from columnar import columnar
    tempList = []
    requestHeaders = {'X-API-KEY': apiKey}
    getOpenIncidentsQuery = query
    getOpenIncidentsQuery.update({"draft":"false"})
    url = f"{baseURL}/{subDomain}/incidents"
    response = requests.get(url, headers=requestHeaders, params=getOpenIncidentsQuery)
    if response.status_code == 200 and len(response.json()) > 0:
        r = json.loads(response.text)['data']
        #print(r)
        for row in r:
            if row['last_incident_type'] != 'resolved':
                tempList.append([row['id'],row['end_time'],row['start_time'],row['last_incident_type'],row['title']])
    if len(tempList) > 0:
        print(f'  = There are currently {len(tempList)} open incidents:')
        print(columnar(tempList, headers=openIncidentsHeader, no_borders=True))
        print()
        return tempList
    else:
        print()
        print('  = There are no open incidents at this time.')
        print()
        return False
#
def createIncident(baseURL, subDomain, serviceID, query, requestHeaders, incidentTypes, serviceStatusTypes):
    incidentTypeInput = ''
    serviceStatusInput = ''
    url = f"{baseURL}/{subDomain}/incidents"
    incidentTitle = input('  = Please provide a short name for this Incident:  ')
    print()
    incidentBody = input('  = Please provide a description of this update:  ')
    print()
    while True:
        try:
            startDate = input('  = Enter a start date in this format YYYY-MM-DD:  ')
            datetime.strptime(startDate, '%Y-%m-%d')
            break
        except:
            print(startDate + ' is invalid. Please try again: '),
            continue
    while True:
        try:
            startTime = input('  = Enter a start time in 24-hour format (HH:MM): ')   # fix this to take time in US Central
            datetime.strptime(startTime, '%H:%M').time()
            break
        except:
            print(f' >>> {startTime} is invalid. Please try again: '),
            continue
    while incidentTypeInput not in incidentTypes:
        incidentTypeInput = input("  = Incident type: (i)nvestigating, (r)esolved, ide(n)tified, (m)onitoring > ")
        print()
    incidentType = str(incidentTypes.get(incidentTypeInput))
    while serviceStatusInput not in serviceStatusTypes:
        serviceStatusInput = input("  = Current service status: (dp)egraded performance, (u)p, (d)own ")
        print()
    serviceStatus = str(serviceStatusTypes.get(serviceStatusInput))
    payload = {"title": incidentTitle, 
               "start_time": f"{startDate} {startTime}",
               "incident_type": incidentType,
               "body": incidentBody,
               "service_statuses": [
                    {
                        "service_id": serviceID,
                        "status": serviceStatus
                    }]
                }
    response = requests.post(url, headers=requestHeaders, params=query, json=payload)
    if response.status_code == 200:
        response = json.loads(response.text)
        print('  = Incident created successfully:')
        print()
        print(f"  = ID:          {response['id']}")
        print(f"  = Title:       {response['title']}")
        print(f"  = Author:      {response['author']}")
        print(f"  = Start Time:  {response['start_time']}")
        print()
        return response
    else:
        print('  = Something went wrong. Please try again.')
#
#while True:
allOpenIncidents = getOpenIncidents(baseURL, subDomain, apiKey, query)
#
while myChoice not in ['c', 'u', 'r', 'l', 'i', 'q']:
    print()
    print('  = Please select an option:')
    print()
    #print('  = (l)ist open incidents')
    print('  = (i)nfo for a specific incident')
    print('  = (c)reate a new incident')
    print('  = (u)pdate an existing incident')
    print('  = (r)esolve an existing incident')
    print('  = (q)uit')
    print()
    myChoice = input('  > ').lower().strip()
    print()
#
if myChoice == 'c':
    createIncident(baseURL, subDomain, serviceID, query, requestHeaders, incidentTypes, serviceStatusTypes)
if myChoice == "i":
    incidentID = input('  = Please provide the ID of the Incident:  ')
    print()
    response = getIncident(baseURL, subDomain, requestHeaders, incidentID)
    #if response:
    #    print()
    #    print(f'  = ID:           {response["id"]}')
    #    print(f'  = Author:       {response["author"]}')
    #    print(f'  = Title:        {response["title"]}')
    #    print(f'  = Start Time:   {response["start_time"]}')
    #    print(f'  = Last Update:  {response["updated_at"]}')
    #    print(f'  = End Time:     {response["end_time"]}')
    #    #print(f'  = Status:       {response["last_incident_type"]}')
    print()
elif myChoice == 'u':
    updateIncident(baseURL, subDomain, requestHeaders, query, incidentTypes, serviceStatusTypes)
elif myChoice == 'r':
    incidentID = ''
    thisIncident = ''
    yesNo = ''
    openIncidents = []
    for row in allOpenIncidents:
        openIncidents.append(row[0])
    while incidentID not in [str(row) for row in openIncidents]:
        #while myIncident not in openIncidents:
        print()
        incidentID = input('  = Please provide the ID of the Incident to resolve:  ')
        print()
    print()
    for row in allOpenIncidents:
        if str(row[0]) == incidentID:
            #thisIncident = getIncident(baseURL, subDomain, requestHeaders, incidentID)
            #thisIncident = row
            print(f'  = You have selected to resolve the following incident:')
            print()
            print(f'  = ID:    {row[0]}')
            print(f'  = Title: {row[4]}')
            print()
            while yesNo not in ['y','n']:
                yesNo = input('  = Are you sure you want to resolve this incident (y/n)? ').strip().lower()
                print()
            if yesNo == 'y':
                resolveIncident(baseURL, subDomain, requestHeaders, row)
            else:
                print('  = Incident resolution cancelled.')
                print()
                #sys.exit()
elif myChoice == 'l':
    openIncidents = getOpenIncidents(baseURL, subDomain, apiKey, query)
    if len(openIncidents) > 0:
        table = columnar(openIncidents, openIncidentsHeader, no_borders=True)
        print(table)
        print()
    else:
        print('  = There are no open incidents at this time.')
else:
    print()
    print('  >>> Exiting Incident Management without changes <<<')
    print()
#while again not in ['y','n']:
#    again = input("Perform another incident management action (y/n)? ").strip().lower()
#    print()
#if again != 'y': break
#else:
#    again = ''
#    myChoice = ''
#print()