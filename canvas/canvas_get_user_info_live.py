#!/usr/bin/python
#
import sys
import requests
import urllib
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import logScriptStart
#
def fetch_user_info(searchTerm, canvasApi, canvasToken, canvasAccountId):
    """
    Fetch user information from Canvas using the REST API.
    Returns the first exact match for NetID, UIN, or Email, or None if not found.
    """
    canvasEndpoint = f"accounts/{canvasAccountId}/users"
    if searchTerm:
        canvasEndpoint += f"?search_term={searchTerm}"
    url = urllib.parse.urljoin(canvasApi, canvasEndpoint)
    headers = {"Authorization": f"Bearer {canvasToken}"}
    params = {"per_page": 100}
    #
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error: Canvas API request failed with status {response.status_code}")
            return None
        searchResults = response.json()
        if not isinstance(searchResults, list):
            print("Error: Unexpected response format from Canvas API.")
            return None
        while 'next' in response.links:
            response = requests.get(response.links['next']['url'], headers=headers, params=params)
            searchResults.extend(response.json())
        # Only return the first exact match (by NetID, UIN, or Email)
        for user in searchResults:
            if (
                user.get("login_id", "").lower() == searchTerm.lower()
                or user.get("sis_user_id", "").lower() == searchTerm.lower()
                or user.get("integration_id", "").lower() == searchTerm.lower()
                or user.get("email", "").lower() == searchTerm.lower()
            ):
                return user
        return None
    except Exception as e:
        print(f"Error: {e}")
        print()
        return None
#
def display_user_info(user):
    """
    Display a single user's information in a readable format.
    """
    if not user:
        print("User Not Found")
    else:
        print("#--------------------------------------")
        print("#  Canvas ID:", user.get("id"))
        print("#        UIN:", user.get("integration_id"))
        print("#       Name:", user.get("name"))
        print("#      NetID:", user.get("sis_user_id"))
        print("#      Email:", user.get("email"))
        print("# Created At:", user.get("created_at"))
        print("#--------------------------------------")
    print('')
#
def main():
    """
    Main entry point for the script. Prompts for a user identifier and displays user info.
    """
    #logScriptStart()
    realmData = realm()
    canvasApi = realmData['canvasApi']
    canvasToken = realmData['canvasToken']
    canvasAccountId = realmData['canvasAccountId']
    #
    while True:
        print('')
        searchTerm = input("Enter NetID or UIN: ").strip()
        print('')
        #
        user = fetch_user_info(searchTerm, canvasApi, canvasToken, canvasAccountId)
        display_user_info(user)
        #
        again = input("Lookup another Canvas user (y/n)? ").strip().lower()
        if again != 'y':
            break
        else: print()
#
if __name__ == "__main__":
    main()
