#!/usr/bin/python

import sys
import requests
import urllib
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import logScriptStart

def fetch_user_info(searchTerm, canvasApi, canvasToken, canvasAccountId):
    """Fetch user information from Canvas."""
    canvasEndpoint = f"accounts/{canvasAccountId}/users"
    if searchTerm:
        canvasEndpoint += f"?search_term={searchTerm}"
    url = urllib.parse.urljoin(canvasApi, canvasEndpoint)
    headers = {"Authorization": f"Bearer {canvasToken}"}
    params = {"per_page": 100}

    response = requests.get(url, headers=headers, params=params)
    searchResults = response.json()

    while 'next' in response.links:
        response = requests.get(response.links['next']['url'], headers=headers, params=params)
        searchResults.extend(response.json())

    return searchResults

def display_user_info(searchResults):
    """Display user information."""
    if not searchResults:
        print("User Not Found")
    else:
        for user in searchResults:
            print("#--------------------------------------")
            print("#  Canvas ID:", user["id"])
            print("#        UIN:", user["integration_id"])
            print("#       Name:", user["name"])
            print("#      NetID:", user["sis_user_id"])
            print("# Created At:", user["created_at"])
            print("#--------------------------------------")
    print('')

def main():
    """Main entry point for the script."""
    #logScriptStart()
    realmData = realm()
    canvasApi = realmData['canvasApi']
    canvasToken = realmData['canvasToken']
    canvasAccountId = realmData['canvasAccountId']

    print('')
    searchTerm = input("Enter NetID, UIN or Email: ")
    print('')

    searchResults = fetch_user_info(searchTerm, canvasApi, canvasToken, canvasAccountId)
    display_user_info(searchResults)

if __name__ == "__main__":
    main()