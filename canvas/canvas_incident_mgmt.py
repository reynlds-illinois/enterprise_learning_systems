#!/usr/bin/python
#
import sys, os, requests, json
from datetime import datetime
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
headers = {'Content-Type': 'application/json', 'Accept': 'application/vnd.statushub.v2'}
requestHeaders = {'Content-Type': 'application/json', 'X-API-KEY': apiKey}
query = {'api_version': 'V3-R1'}
sr = []
params = {}
columnHeader = ['id', 'service', 'service_state', 'title', 'created', 'last_update', 'incident_status']
incidentTypes = {'i': 'investigating', 'r': 'resolved', 'n': 'identified'}
serviceStatusTypes = {'dp': 'degraded-performance', 'u': 'up', 'd': 'down'}#
#
def getSingleIncident(baseURL, subDomain, apiKey, query, incidentID):
    requestHeaders = {'X-API-KEY': apiKey}
    url = f"{baseURL}/{subDomain}/incidents/{incidentID}"
    response = requests.get(url, headers=requestHeaders, params=query)
    if response.status_code == 200:
        if len(json.loads(response.text)) > 0:
            return response
#
def getAllCanvasIncidents(baseURL, subDomain, apiKey, query):
    requestHeaders = {'X-API-KEY': apiKey}
    query.update({"draft":"false"})
    url = f"{baseURL}/{subDomain}/incidents"
    response = requests.get(url, headers=requestHeaders, params=query)
    if response.status_code == 200:
        if len(response.json()) > 0:
            return json.loads(response.text)['data']
#
def createNewCanvasIncident(baseURL, subDomain, serviceID, query, requestHeaders, incidentTypes, serviceStatusTypes):
    url = f"{baseURL}/{subDomain}/incidents"
    incidentTitle = input('  = Please provide a short name for this Incident:  ')
    print()
    while True:
        try:
            startDate = input('Enter a start date in this format YYYY-MM-DD:  ')
            datetime.strptime(startDate, '%Y-%m-%d')
            break
        except:
            print(startDate + ' is invalid. Please try again: '),
            continue
    while True:
        try:
            startTime = input('Enter a start time in 24-hour format (HH:MM): ')
            datetime.strptime(startTime, '%H:%M').time()
            break
        except:
            print(startTime + ' is invalid. Please try again: '),
            continue
    while incidentTypeInput not in incidentTypes:
        incidentTypeInput = input("  = Incident type: (i)nvestigating, (r)esolved, ide(n)tified ")
        print()
    incidentType = str(incidentTypes.get(incidentTypeInput))
    while serviceStatusInput not in serviceStatusTypes:
        serviceStatusInput = input("  = Current service status: (d)egraded performance, (u)p, (d)own ")
        print()
    serviceStatus = str(serviceStatusTypes.get(serviceStatusInput))
    payload = {"title": incidentTitle, 
               "incident_type": incidentType,
               "service_statuses": [
                   {"service_id": serviceID,
                    "status_name": serviceStatus}]}
    response = requests.post(url, headers=requestHeaders, params=query, json=payload)
    if response.status_code == 200:






### V2 STARTS HERE ###

def newIncident(baseURL, apiKey, serviceID, domain, incidentTypes, serviceStatusTypes):
    serviceStatusInput = ''
    incidentTypeInput = ''
    headers = {'Content-Type': 'application/json', 'Accept': 'application/vnd.statushub.v2'}
    today = datetime.now().strftime('%Y-%m-%d')
    #startTime = input('Incident start time (in 24-hr format):  ')
    while True:
        startTime = input('Incident start time (in 24-hr format, e.g., 12:30:00):  ')
        try:
            datetime.strptime(startTime, "%H:%M:%S")
            break
        except ValueError:
            print("Invalid time format. Please use HH:MM:SS (24-hour).")
    #
    incidentName = str(input('Please provide a short name for this Incident:  '))
    incidentMessage = str(input('Please provide a short description of the Incident:  '))
    #
    while incidentTypeInput not in incidentTypes:
        incidentTypeInput = input("Incident type: (i)nvestigating, (r)esolved, ide(n)tified ")
    incidentType = str(incidentTypes.get(incidentTypeInput))
    #
    while serviceStatusInput not in serviceStatusTypes:
        serviceStatusInput = input("Current service status: (d)egraded performance, (u)p, (d)own ")
    serviceStatus = str(serviceStatusTypes.get(serviceStatusInput))
    #
    newIncidentURL = str(f'{baseURL}status_pages/{domain}/incidents?api_key={apiKey}&silent=true')
    startTimestamp = str(f'{today} {startTime}')
    payload = {
        "incident": {
            "title": incidentName,
            "start_time": startTimestamp,
            "update": {
                "body": incidentMessage,
                "incident_type": incidentType
            }
        },
        "service_statuses": [
            {
                "service_id": serviceID,
                "status_name": serviceStatus
            }
        ]
    }
    input("Press <ENTER> to continue...")
    r = requests.post(newIncidentURL, headers=headers, json=payload)
    return r.text
#
def getCanvasIncidents(baseURL, apiKey, domain, serviceID, columnHeader):
    acdict = []
    url = f"{baseURL}status_pages/{domain}/incidents?api_key={apiKey}&per_page=100&service_ids={serviceID}"
    ac = requests.get(url).json()
    for row in ac:
        if row['incident_updates'][0]['incident_type'] != 'resolved':
            acdict.append([row['id'],row['incident_updates'][0]['service_statuses'][0]['service_name'], row['incident_updates'][0]['service_statuses'][0]['status_name'], row['title'], row['created_at'], row['incident_updates'][0]['updated_at'], row['incident_updates'][0]['incident_type']])
    if len(acdict) == 0:
        print()
        print('  >>> Canvas @ Illinois currently has no active issues <<<')
        print()
    else:
        print(columnar(acdict, columnHeader))
        return acdict
#
def getAllIncidents(baseURL, apiKey, domain, headers, columnHeader):
    sr = []
    srdict = []
    url = f"{baseURL}status_pages/{domain}/incidents?api_key={apiKey}&per_page=100"
    r = requests.get(url, headers=headers)
    if len(r.json()) > 0:
        sr.extend(r.json())
        while 'next' in r.links:
            r = requests.get(r.links['next']['url'], headers=headers)
            sr.extend(r.json())
    for row in sr:
        srdict.append([row['id'], row['incident_updates'][0]['service_statuses'][0]['service_name'], row['incident_updates'][0]['service_statuses'][0]['status_name'], row['title'], row['created_at'], row['incident_updates'][0]['updated_at'], row['incident_updates'][0]['incident_type']])
    print(columnar(srdict, columnHeader))
    return srdict
#
def updateIncident(baseURL, apiKey, domain, headers, serviceID, incidentID, incidentTypes, serviceStatusTypes):
    updateIncidentURL = str(f'{baseURL}status_pages/{domain}/incidents/{incidentID}?api_key={apiKey}')
    incidentTypeInput = ''
    while incidentTypeInput not in incidentTypes:
        incidentTypeInput = input("Incident type: (i)nvestigating, (r)esolved, ide(n)tified ")
    incidentType = str(incidentTypes.get(incidentTypeInput))
    serviceStatusInput = ''
    while serviceStatusInput not in serviceStatusTypes:
        serviceStatusInput = input("Current service status: (d)egraded performance, (u)p, (d)own ")
    serviceStatus = str(serviceStatusTypes.get(serviceStatusInput))
    incidentMessage = str(input('Please provide a short update for the Incident:  '))
    payload = {
        "update": {
            "body": incidentMessage,
            "incident_type": incidentType
        },
        "service_statuses": [
            {
                "service_id": serviceID,
                "status_name": serviceStatus
            }
        ]
    }
    r = requests.put(updateIncidentURL, headers=headers, json=payload)
    return r.text






# Get incidents for a service ID
serviceIDURL = f"https://api.statushub.io/api/status_pages/{domain}/incidents?api_key={apiKey}&per_page=100&service_ids={serviceID}"
allIncidentsURL = f"https://api.statushub.io/api/status_pages/{domain}/incidents?api_key={apiKey}&per_page=100"
sr = []
r = requests.get(url, headers=headers, data=payload)
if len(r.json()) > 0:
    sr.extend(r.json())
    while 'next' in r.links:
        r = requests.get(r.links['next']['url'], headers=headers, data=payload)
        sr.extend(r.json())


rjson = r.json()
for item in rjson:
    print(item['id'], '-', item['incident_updates'][0]['service_statuses'][0]['service_name'])


for item in r:
    print(f"Incident ID:              {item['id']}")
    print(f"Created At:               {item['created_at']}")
    for object in item['incident_updates']:
        if not object['body']:
            incidentBody = ' '
        else:  incidentBody = object['body']
        print(f"    Incident Created At:  {object['created_at']}")
        print(f"    Incident Headline:    {incidentBody}")
        print(f"    Service Status:       {object['service_statuses'][0]['status_name']}")
        print(f"    Incident Type:        {object['incident_type']}")
        print(f"    Incident Start:       {object['start_time']}")
        print(f"    Incident Updated:     {object['updated_at']}")
    print('==========')





==========

authHeaders = {"Authorization": f"Bearer {canvasToken}"}
