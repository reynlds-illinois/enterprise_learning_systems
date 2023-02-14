#!/usr/bin/python
#
import sys, os, requests, pprint, urllib, json, time, datetime
from datetime import date
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
env = getEnv()
logScriptStart)
canvasToken = env["canvas.ro-api"]
canvasApi = env["canvas.api-prod"]
canvasAccountId = "1"
errors = 0
today = str(date.today().strftime("%Y-%m-%d"))
paginated_search_results = []
print('')
#
search_term = input("Enter CourseID: ")
#
canvas_endpoint = "accounts/1/courses"
if search_term is not None:
    canvas_endpoint += f"?search_term={search_term}"
url = urllib.parse.urljoin(canvasApi, canvas_endpoint)
headers = {"Authorization": f"Bearer {canvasToken}"}
params = {"per_page": 100}
response = requests.get(url, headers=headers, params=params)
search_results = response.json()
while 'next' in response.links:
    response = requests.get(response.links['next']['url'], headers=headers, params=params)
    search_results.extend(response.json())
if search_results is None:
    print("Course Not Found")
else:
    print("")
    for course in search_results:
        if course["sis_course_id"] == search_term:
            print("#--------------------------------------")
            print("#   Canvas ID:",course["id"])
            print("#   Course ID:",course["sis_course_id"])
            print("# Course Name:",course["name"])
            print("#       State:",course["workflow_state"])
            print("#  Created At:",course["created_at"])
            print("#    Start At:",course["start_at"])
            print("#      End At:",course["end_at"])
            print("#   Blueprint:",course["blueprint"])
            print("# Course Link:",f"https://canvas.illinois.edu/courses/{course['id']}")
            print("#--------------------------------------")
    print("")

