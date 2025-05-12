#!/usr/bin/python
#
import sys, requests, json, csv
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import findCanvasCourse
from canvasFunctions import convertDate
from columnar import columnar

# Initialize realm
realm = realm()

# Canvas API setup
canvasQuizApi = realm['canvasQuizApi']
canvasToken = realm['canvasToken']
columnHeaders = ['canvas_course_id', 'uiuc_course_id', 'quiz_id', 'quiz_title']
params = {"per_page": 100}
authHeader = {"Authorization": f"Bearer {canvasToken}"}

bannerTermID = input("Enter the Banner Term ID: ")
bannerTermCourses = []
newQuizzes = []
newQuizCourses = []
params = {"per_page": 100}

# Load courses from CSV file
with open("/var/lib/canvas-mgmt/config/canvas_courses.csv", 'r') as coursesCSV:
    reader = csv.reader(coursesCSV)
    allCourses = [row for row in reader]  # Convert the CSV rows into a list of lists

# Filter courses based on the Banner Term ID
for course in allCourses:
    if course[8] == bannerTermID:
        bannerTermCourses.append(course)

# Print the number of courses found for the given Banner Term ID
for course in bannerTermCourses:
    searchResults = []
    canvasCourseID = course[0]
    uiucCourseID = course[1]
    url = f"{canvasQuizApi}courses/{canvasCourseID}/quizzes"
    print(url)
    response = requests.get(url, headers=authHeader, params=params)

    # Check if the response is valid
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code} for course {canvasCourseID}")
        continue

    try:
        data = response.json()  # Attempt to parse JSON
    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON for course {canvasCourseID}")
        continue

    # Check if the response contains quizzes
    if len(data) > 0:
        searchResults.extend(data)
        while 'next' in response.links:
            response = requests.get(response.links['next']['url'], headers=authHeader, params=params)
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"Error: Unable to decode JSON for course {canvasCourseID} on subsequent page")
                break
            searchResults.extend(data)

    # Check if the course has New Quizzes
    if len(searchResults) > 0:
        for line in searchResults:
            newQuizzes.append([canvasCourseID, uiucCourseID, line.get("id"), line.get("title")])
            # Add to newQuizCourses only if the pair is not already in the list
            if [canvasCourseID, uiucCourseID] not in newQuizCourses:
                newQuizCourses.append([canvasCourseID, uiucCourseID])

# Print the results
print(columnar(newQuizzes, columnHeaders, no_borders=True))
print()
print(f'  ==> Total number of courses for Banner Term {bannerTermID}: ', len(bannerTermCourses))
print()
print('  ==> Total number of courses with New Quizzes found in these courses: ', len(newQuizCourses))
print()
print('  ==> Total number of quizzes found in these courses:: ', len(newQuizzes))
print("\n\n")
