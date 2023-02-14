#!/usr/bin/python
#
import sys, os, requests, pprint, urllib, json, time, datetime
from datetime import date
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
env = getEnv()
logScriptStart()
canvasToken = env["canvas.ro-api"]
canvasApi = env["canvas.api-prod"]
canvasAccountId = "1"
errors = 0
today = str(date.today().strftime("%Y-%m-%d"))
search_results = []
#
print('')
search_term = input("Enter NetID or UIN: ")
print('')
#
canvas_endpoint = "accounts/1/users"
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
    print("User Not Found")
else:
    for user in paginated_search_results:
        #if user["login_id"] == search_term:
        print("#--------------------------------------")
        print("#  Canvas ID:",user["id"])
        print("#        UIN:",user["integration_id"])
        print("#       Name:",user["name"])
        print("#      NetID:",user["sis_user_id"])
        print("# Created At:",user["created_at"])
        print("#--------------------------------------")
print('')
