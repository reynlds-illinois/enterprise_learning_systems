#!/usr/bin/python
#
import sys, requests, urllib.parse
from datetime import date
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import logScriptStart, realm

# Initialize environment
logScriptStart()
answer = ''
realm = realm()
canvasToken = realm["canvasToken"]
canvasApi = realm["canvasApi"]
headers = {"Authorization": f"Bearer {canvasToken}"}
params = {"per_page": 100}

print("")

# Prompt user for CourseID
search_term = input("Enter CourseID: ").strip()
if not search_term:
    print("Error: CourseID cannot be empty.")
    sys.exit(1)

def paginate_canvas_api(url, headers, params):
    """
    Generator function to handle paginated Canvas API responses.
    """
    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Ensure HTTP errors are raised
        yield from response.json()  # Yield each item in the current page
        url = response.links.get('next', {}).get('url')  # Get the next page URL

# Build the Canvas API endpoint
canvas_endpoint = f"accounts/1/courses?search_term={search_term}"
url = urllib.parse.urljoin(canvasApi, canvas_endpoint)

# Use the generator to fetch all pages
try:
    all_results = list(paginate_canvas_api(url, headers, params))
except requests.exceptions.RequestException as e:
    print(f"Error fetching data from Canvas API: {e}")
    sys.exit(1)

# Process search results
if not all_results:
    print("Course Not Found")
else:
    print("")
    for course in all_results:
        if course.get("sis_course_id") == search_term:
            print("#--------------------------------------")
            print(f"#   Canvas ID: {course.get('id', 'N/A')}")
            print(f"#   Course ID: {course.get('sis_course_id', 'N/A')}")
            print(f"# Course Name: {course.get('name', 'N/A')}")
            print(f"#       State: {course.get('workflow_state', 'N/A')}")
            print(f"#  Created At: {course.get('created_at', 'N/A')}")
            print(f"#    Start At: {course.get('start_at', 'N/A')}")
            print(f"#      End At: {course.get('end_at', 'N/A')}")
            print(f"#   Blueprint: {course.get('blueprint', 'N/A')}")
            print(f"# Course Link: https://canvas.illinois.edu/courses/{course.get('id', 'N/A')}")
            print("#--------------------------------------")
    print("")
while answer != 'y' and answer != 'n':
    answer = input('Would you like to see course details (y/n)?').lower().strip()
    print()
if answer == 'y':
    pprint(course)
print()
