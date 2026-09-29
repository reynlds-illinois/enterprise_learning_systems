#!/usr/bin/python
#
import sys, urllib.parse, requests
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm, canvasJsonDates, canvasGetUserInfoLive
#
print('')
realm = realm()
print(f'Connected to {realm["envLabel"]} - {realm["canvasUrl"]}')
print('')
canvasAPI = realm['canvasApi']
canvasAuth = {"Authorization": f"Bearer {realm['canvasToken']}"}
enrollStates = ["active", "invited", "creation_pending", "inactive", "completed", "rejected", "deleted"]
#
def val(value):
    return 'n/a' if value in (None, '') else value

def formatSeconds(seconds):
    if not seconds:
        return 'n/a'
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f'{hours}:{minutes:02d}:{secs:02d}'

def printEnrollment(enroll):
    user = enroll.get('user', {})
    print('>>> Enrollment details:')
    print()
    print(f'    Enroll ID:        {val(enroll.get("id"))}')
    print(f'    Enroll State:     {val(enroll.get("enrollment_state"))}')
    print(f'    Role:             {val(enroll.get("role"))}')
    print(f'    Type:             {val(enroll.get("type"))}')
    print(f'    Name:             {val(user.get("name"))}')
    print(f'    NetID:            {val(enroll.get("sis_user_id"))}')
    print(f'    Canvas Course ID: {val(enroll.get("course_id"))}')
    print(f'    SIS Course ID:    {val(enroll.get("sis_course_id"))}')
    print(f'    Canvas Section:   {val(enroll.get("course_section_id"))}')
    print(f'    SIS Section ID:   {val(enroll.get("sis_section_id"))}')
    print(f'    Created:          {val(enroll.get("created_at"))}')
    print(f'    Updated:          {val(enroll.get("updated_at"))}')
    print(f'    Start:            {val(enroll.get("start_at"))}')
    print(f'    End:              {val(enroll.get("end_at"))}')
    print(f'    Last Activity:    {val(enroll.get("last_activity_at"))}')
    print(f'    Total Activity:   {formatSeconds(enroll.get("total_activity_time"))}')
    if enroll.get('type') == 'StudentEnrollment':
        grades = enroll.get('grades') or {}
        print(f'    Current Score:    {val(grades.get("current_score"))}')
        print(f'    Current Grade:    {val(grades.get("current_grade"))}')
        print(f'    Final Score:      {val(grades.get("final_score"))}')
        print(f'    Final Grade:      {val(grades.get("final_grade"))}')
    print()
#
while True:
    canvasUser = None
    while not canvasUser:
        searchTerm = input("Enter the NetID, UIN or E-mail of the user (q to quit): ").strip()
        if searchTerm.lower() == 'q':
            sys.exit(0)
        if not searchTerm:
            continue
        canvasUser = canvasGetUserInfoLive(searchTerm, canvasAPI, canvasAuth)
        if not canvasUser:
            print("User not found. Please try again.")
            print()
    courseInput = ''
    while not courseInput:
        courseInput = input("Enter the Canvas course ID or SIS course ID: ").strip()
    if courseInput.isdigit():
        courseRef = courseInput
    else:
        courseRef = urllib.parse.quote(f'sis_course_id:{courseInput}', safe='')
    url = f"{canvasAPI}courses/{courseRef}/enrollments"
    params = {"user_id": canvasUser['id'], "state[]": enrollStates, "per_page": 100}
    print()
    response = requests.get(url, headers=canvasAuth, params=params)
    if response.status_code == 404:
        print(f"Course not found: {courseInput}")
        print()
        continue
    if response.status_code != 200:
        print(f"Error: Canvas API request failed with status {response.status_code}")
        print(f"  {response.text}")
        print()
        continue
    enrollments = response.json()
    while 'next' in response.links:
        response = requests.get(response.links['next']['url'], headers=canvasAuth)
        enrollments.extend(response.json())
    if not enrollments:
        print(f"No enrollment found for {searchTerm} in course {courseInput}.")
        print()
        continue
    enrollments = canvasJsonDates(enrollments)
    for enroll in enrollments:
        printEnrollment(enroll)