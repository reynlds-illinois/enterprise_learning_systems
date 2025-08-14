#!/usr/bin/python
#
import sys, requests
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import findCanvasCourse
from canvasFunctions import canvasCourseInfo
from canvasFunctions import convertDate
from canvasFunctions import canvasGetNetID
from columnar import columnar

# Initialize realm
realm = realm()

# Canvas API setup
canvasAPI = realm['canvasApi']
canvasToken = realm['canvasToken']
params = {"per_page": 100}
canvasAuth = {"Authorization": f"Bearer {canvasToken}"}

# Get course ID from user
uiucCourseID = input('Please enter the course ID:  ')
print()
canvasCourseID = findCanvasCourse(uiucCourseID)
url = f"{canvasAPI}audit/course/courses/{canvasCourseID}"

# Fetch course audit data
courseAudit = requests.get(url, headers=canvasAuth, params=params)

# Handle non-200 responses
if courseAudit.status_code != 200:
    print(f"Error: Failed to fetch course audit data. Status code: {courseAudit.status_code}")
    print(f"Response: {courseAudit.text}")
    print()
    sys.exit(1)

# Parse JSON response
try:
    courseAudit = courseAudit.json()
except ValueError:
    print("Error: Failed to parse JSON response from Canvas API.")
    sys.exit(1)
    print()

# Validate response structure
if 'events' not in courseAudit or 'linked' not in courseAudit:
    print("Error: Unexpected response structure from Canvas API.")
    sys.exit(1)
    print()

# Define event types and table headers
eventTypes = ['concluded', 'created', 'copied_from', 'published', 'updated']
courseEventsHeader = ['TIMESTAMP', 'COURSE_ID', 'EVENT_SRC', 'EVENT_TYPE', 'SOURCE_COURSE', 'INITIATOR', 'DETAILS']

courseEventsTable = []

# Process course events
for item in courseAudit['events']:
    print('Parsing events...please wait...')
    createdAt = convertDate(item['created_at'])
    eventSource = item['event_source']
    eventType = item['event_type']
    if eventType == 'copied_from':
        sourceCourseTemp = canvasCourseInfo(item['links']['copied_from'], canvasAPI, canvasAuth)['sis_course_id']
    else: sourceCourseTemp = 'n/a'
    if item['links']['course']:
        courseTemp = canvasCourseInfo(item['links']['course'], canvasAPI, canvasAuth)['sis_course_id']
    else: courseTemp = 'n/a'
    if item['links']['user']:
        userTemp = canvasGetNetID(item['links']['user'])[4]
    else: userTemp = 'n/a'
    if item['event_data']:
        eventData = item['event_data']
        eventData = '\n'.join([f'{k}: {v}' for k, v in eventData.items()])
    else: eventData = 'n/a'
    # Append event to table
    courseEventsTable.append([createdAt, courseTemp, eventSource, eventType, sourceCourseTemp, userTemp, eventData])

# Print course events table
if len(courseEventsTable) > 0:
    print(columnar(courseEventsTable, courseEventsHeader))
else:
    print(f'>>> No audit info recorded for {uiucCourseID}.')
print()