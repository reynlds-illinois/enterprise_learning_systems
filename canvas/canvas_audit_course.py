#!/usr/bin/python
#
import sys, requests
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import findCanvasCourse
from canvasFunctions import convertDate
from columnar import columnar

# Initialize realm
realm = realm()

# Canvas API setup
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
params = {"per_page": 100}
headers = {"Authorization": f"Bearer {canvasToken}"}

# Get course ID from user
uiucCourseID = input('Please enter the course ID:  ')
print()
canvasCourseID = findCanvasCourse(uiucCourseID)
url = f"{canvasApi}audit/course/courses/{canvasCourseID}"

# Fetch course audit data
courseAudit = requests.get(url, headers=headers, params=params)

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

courseEventsTable = []

# Define event types and table headers
eventTypes = ['concluded', 'created', 'copied_from', 'published', 'updated']
courseEventsHeader = ['TIMESTAMP', 'COURSE_ID', 'EVENT_SRC', 'EVENT_TYPE', 'INITIATOR', 'DETAILS']

# Process course events
for item in courseAudit['events']:
    if item['event_type'] in eventTypes:
        userTemp = '-'
        sourceCourseTemp = '-'
        courseTemp = '-'

        # Get user information
        if item['links']['user']:
            for row in courseAudit['linked']['users']:
                if row['id'] == item['links']['user']:
                    userTemp = row['sis_user_id']

        # Get source course information
        if item['event_type'] == 'copied_from':
            for row in courseAudit['linked']['courses']:
                if row['id'] == item['links']['copied_from']:
                    sourceCourseTemp = row['sis_course_id']

        # Get course information
        if item['links']['course']:
            for row in courseAudit['linked']['courses']:
                if row['id'] == item['links']['course']:
                    courseTemp = row['sis_course_id']

        # Extract event details
        createdAt = convertDate(item['created_at'])
        eventSource = item['event_source']
        eventType = item['event_type']
        courseID = courseTemp
        eventData = item['event_data']
        eventData = '\n'.join([f'{k}: {v}' for k, v in eventData.items()])

        # Append event to table
        courseEventsTable.append([createdAt, courseID, eventSource, eventType, userTemp, eventData])

# Print course events table
print(columnar(courseEventsTable, courseEventsHeader))
print()
