import sys, requests
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import findCanvasCourse
from canvasFunctions import canvasCourseInfo
from canvasFunctions import convertDate
from canvasFunctions import canvasGetNetID
from canvasFunctions import canvasJsonDates
from columnar import columnar
#
# Initialize realm
realm = realm()
#
# Canvas API setup
canvasAPI = realm['canvasApi']
canvasToken = realm['canvasToken']
params = {"per_page": 100}
canvasAuth = {"Authorization": f"Bearer {canvasToken}"}
#
# Define event types and table headers
eventTypes = ['concluded', 'created', 'copied_from', 'published', 'updated']
courseEventsHeader = ['TIMESTAMP', 'EVENT_TYPE', 'CANVAS_COURSE_ID', 'UIUC_COURSE_ID', 'INITIATOR']
#
def findCanvasCourse(courseId):
    """Return Canvas course ID when UIUC course ID is provided"""
    import csv
    from pprint import pprint
    csv_file = csv.reader(open("/var/lib/canvas-mgmt/config/canvas_courses.csv", "r", encoding="utf-8"), delimiter=",")
    for row in csv_file:
        if courseId == row[1]:
            return str(row[0])
#
def canvasGetNetID(canvasUserID):
    import csv, os, sys
    with open('/var/lib/canvas-mgmt/config/canvas_users.csv', 'r') as csvFile:
        reader = csv.reader(csvFile)
        for row in reader:
            if row[0] == canvasUserID:
                return row[1]
            else:
                continue
#
def getUIUCCourseID(canvasCourseID):
    import csv, os, sys
    with open('/var/lib/canvas-mgmt/config/canvas_courses.csv', 'r') as csvFile:
        reader = csv.reader(csvFile)
        for row in reader:
            if row[0] == str(canvasCourseID):
                return str(row[1])
#
answer = ''
# Get course ID from user
uiucCourseID = input('Please enter the course ID:  ')
print()
origCanvasCourseID = findCanvasCourse(uiucCourseID)
#
defaultTemplateCourse = 57083
courseCopies = []
canvasCourseID = '60925'
#eventCount = 2
#while eventCount > 1:
#
courseCopies = []
currentCanvasCourseID = origCanvasCourseID
#
while True:
    url = f"{canvasAPI}audit/course/courses/{currentCanvasCourseID}"
    courseAudit = requests.get(url, headers=canvasAuth, params=params)
    if courseAudit.status_code != 200:
        print(f"Failed to fetch audit for course {currentCanvasCourseID}")
        break
    courseAudit = courseAudit.json()
    foundCopy = False
    for item in courseAudit['events']:
        if item['event_type'] == 'copied_from' and item['event_source'] == 'api_in_app':
            eventDate = item['created_at']
            eventSource = item['event_source']
            eventType = item['event_type']
            sourceCanvasCourseID = item['links']['copied_from']
            copyCanvasUserID = item['links']['user']
            sourceUIUCCourseID = getUIUCCourseID(sourceCanvasCourseID)
            copyUIUCNetID = canvasGetNetID(copyCanvasUserID)
            courseCopies.append([eventDate, eventType, sourceCanvasCourseID, sourceUIUCCourseID, copyUIUCNetID])
            currentCanvasCourseID = sourceCanvasCourseID
            foundCopy = True
            break  # Only follow the first found copy event
    if not foundCopy or int(currentCanvasCourseID) == int(defaultTemplateCourse):
        break
#
courseCopies = canvasJsonDates(courseCopies)
table = columnar(courseCopies, courseEventsHeader, min_column_width=23)
print()
print(f">>> Course Copy History for UIUC Course ID {uiucCourseID} <<<")
print()
print(table)
print()
