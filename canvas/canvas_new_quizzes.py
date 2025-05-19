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
lookupType = ''

# Prompt the user for lookup type
while lookupType not in ['t', 'c']:
    lookupType = input("Enter 't' to search by Banner Term ID or 'c' to search by a single course: ").strip().lower()
    print()

# Initialize lists to store courses and quizzes
allCourses = []
bannerTermCourses = []
newQuizzes = []
newQuizCourses = []

# Load courses from CSV file
with open("/var/lib/canvas-mgmt/config/canvas_courses.csv", 'r') as coursesCSV:
    reader = csv.reader(coursesCSV)
    allCourses = [row for row in reader]  # Convert the CSV rows into a list of lists

if lookupType == 't':
    # Banner Term Lookup
    bannerTermID = input("Enter the Banner Term ID: ").strip()
    for course in allCourses:
        if course[8] == bannerTermID:
            bannerTermCourses.append(course)

    print(f"\nFound {len(bannerTermCourses)} courses for Banner Term ID {bannerTermID}.\n")

    # Process each course in the Banner Term
    for course in bannerTermCourses:
        canvasCourseID = course[0]
        uiucCourseID = course[1]
        url = f"{canvasQuizApi}courses/{canvasCourseID}/quizzes"
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
        searchResults = []
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
                if [canvasCourseID, uiucCourseID] not in newQuizCourses:
                    newQuizCourses.append([canvasCourseID, uiucCourseID])

elif lookupType == 'c':
    # Single Course Lookup
    uiucCourseID = input("Enter the UIUC Course ID: ").strip()
    courseFound = False

    for course in allCourses:
        if course[1] == uiucCourseID:
            courseFound = True
            canvasCourseID = course[0]
            url = f"{canvasQuizApi}courses/{canvasCourseID}/quizzes"
            response = requests.get(url, headers=authHeader, params=params)

            # Check if the response is valid
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code} for course {canvasCourseID}")
                break

            try:
                data = response.json()  # Attempt to parse JSON
            except json.JSONDecodeError:
                print(f"Error: Unable to decode JSON for course {canvasCourseID}")
                break

            # Check if the response contains quizzes
            searchResults = []
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
                print(f"\nNew Quizzes for course {uiucCourseID} (Canvas Course ID: {canvasCourseID}):")
                print(columnar(newQuizzes, columnHeaders, no_borders=True))
            else:
                print(f"No New Quizzes found for course {uiucCourseID} (Canvas Course ID: {canvasCourseID}).")
            break

    if not courseFound:
        print(f"Error: Course with UIUC Course ID {uiucCourseID} not found.")

else:
    print("Invalid input. Please enter 'term' or 'course'.")

# Print summary for Banner Term Lookup
if lookupType == 't':
    print(columnar(newQuizzes, columnHeaders, no_borders=True))
    print()
    print(f'  ==> Total number of courses for Banner Term {bannerTermID}: ', len(bannerTermCourses))
    print()
    print('  ==> Total number of courses with New Quizzes: ', len(newQuizCourses))
    print()
    print('  ==> Total number of New Quizzes found in these courses: ', len(newQuizzes))
    print("\n\n")
