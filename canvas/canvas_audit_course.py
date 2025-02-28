import cx_Oracle, sys, csv, requests, time, datetime, pytz
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import logScriptStart
from canvasFunctions import realm
from canvasFunctions import findCanvasCourse
from canvasFunctions import convertDate
from columnar import columnar
from datetime import datetime
#
realm = realm()
#
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
params = {"per_page": 100}
headers = {"Authorization": f"Bearer {canvasToken}"}
uiucCourseID = input('Please enter the course ID:  ')
canvasCourseID = findCanvasCourse(uiucCourseID)
url = f"{canvasApi}audit/course/courses/{canvasCourseID}"
#
courseAudit = requests.get(url, headers=headers, params=params)
if courseAudit.status_code == 200:
    courseAudit = courseAudit.json()
courseEvents = courseAudit['events']
courseLinked = courseAudit['linked']
courseLinks = courseAudit['links']
sourceCourseTemp = ''
courseTemp = ''
userTemp = ''
courseEventsTable = []
#
eventTypes = ['concluded', 'created', 'copied_from', 'published', 'updated']
courseEventsHeader = ['TIMESTAMP','COURSE_ID','EVENT_SRC','EVENT_TYPE','INITIATOR','DETAILS']
for item in courseAudit['events']:
    if item['event_type'] in eventTypes:
        if item['links']['user']:
            for row in courseAudit['linked']['users']:
                if row['id'] == item['links']['user']:
                    userTemp = row['sis_user_id']
                    netID = userTemp
        else: userTemp = '-'
        if item['event_type'] == 'copied_from':
            for row in courseAudit['linked']['courses']:
                if row['id'] == item['links']['copied_from']:
                    #sourceCourseTemp = row['sis_course_id']
                    netID = row['sis_course_id']
        else: sourceCourseTemp = '-'
        if item['links']['course']:
            for row in courseAudit['linked']['courses']:
                if row['id'] == item['links']['course']:
                    courseTemp = row['sis_course_id']
        else: courseTemp = '-'
        createdAt = convertDate(item['created_at'])
        eventSource = item['event_source']
        eventType = item['event_type']
        courseID = courseTemp
        sourceCourse = sourceCourseTemp
        eventData = item['event_data']
        eventData = '\n'.join([f'{k}: {v}' for k, v in eventData.items()])
        courseEventsTable.append([createdAt, courseID, eventSource, eventType, netID, eventData])
print(columnar(courseEventsTable, courseEventsHeader))
print()
