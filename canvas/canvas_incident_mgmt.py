#!/usr/bin/python
#
import sys, os, requests, json, pytz
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
incidentTypes = {'i': 'investigating', 'r': 'resolved', 'n': 'identified', 'm': 'monitoring'}
serviceStatusTypes = {'dp': 'degraded-performance', 'u': 'up', 'd': 'down'}
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
    incidentTypeInput = ''
    serviceStatusInput = ''
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
            startTime = input('Enter a start time in 24-hour format (HH:MM): ')   # fix this to take time in US Central
            datetime.strptime(startTime, '%H:%M').time()
            break
        except:
            print(startTime + ' is invalid. Please try again: '),
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
        print(f'  = ID:          {response['id']})
        print(f'  = Title:       {response['title']})
        print(f'  = Author:      {response['author']})
        print(f'  = Start Time:  {response['start_time']})
        print()
        return response
    else:
        print('  = Something went wrong. Please try again.')