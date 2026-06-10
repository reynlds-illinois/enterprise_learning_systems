#!/usr/bin/python
#
import sys, os, requests, json
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from canvasFunctions import realm
#from canvas_get_user_info_live import fetch_user_info, display_user_info

realm = realm()
canvasAPI = realm['canvasApi']
canvasToken = realm['canvasToken']
canvasAuth = {"Authorization": f"Bearer {canvasToken}"}
accountID = "1"

def fetch_user_info(searchTerm, canvasApi, canvasToken, canvasAccountId):
    """
    Fetch user information from Canvas using the REST API.
    Returns the first exact match for NetID, UIN, or Email, or None if not found.
    """
    #canvasEndpoint = f"accounts/{canvasAccountId}/users"
    #if searchTerm:
    #    canvasEndpoint = f"?search_term={searchTerm}"
    #url = urllib.parse.urljoin(canvasApi, canvasEndpoint)
    url = f"{canvasApi}accounts/{canvasAccountId}/users?search_term={searchTerm}"
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

def display_user_info(user):
    """
    Display a single user's information in a readable format.
    """
    if not user:
        print("User Not Found")
    else:
        print("  #--------------------------------------")
        print("  #  Canvas ID:", user.get("id"))
        print("  #        UIN:", user.get("integration_id"))
        print("  #       Name:", user.get("name"))
        print("  #      NetID:", user.get("sis_user_id"))
        print("  #      Email:", user.get("email"))
        print("  # Created At:", user.get("created_at"))
        print("  #--------------------------------------")
    print('')

print()
print("=== Create New Canvas User ===")
print()

firstname = input("  > First Name:  ").strip()
lastname  = input("  > Last Name:   ").strip()
netid     = input("  > NetID:       ").strip()
uin       = input("  > UIN:         ").strip()
email     = input("  > Email:       ").strip()

fullname  = f"{firstname} {lastname}"

print()
print("--- User to be created ---")
print(f"  = Name:   {fullname}")
print(f"  = NetID:  {netid}")
print(f"  = UIN:    {uin}")
print(f"  = Email:  {email}")
print()

confirm = input("Confirm creation (y/n)?  ").strip().lower()
if confirm != 'y':
    print()
    print("  >>> Cancelled. No user was created.")
    print()
    sys.exit(0)

# Canvas account to create the user under (1 = root account)
createUserURL = f"{canvasAPI}accounts/{accountID}/users"

payload = {
    "user[name]":fullname,
    "user[display_name]":fullname,
    "user[short_name]":fullname,
    "user[sortable_name]":f"{lastname}, {firstname}",
    "pseudonym[unique_id]":netid,
    "pseudonym[sis_user_id]":netid,
    "pseudonym[integration_id]":uin,
    "communication_channel[address]":email,
    "communication_channel[type]":"email",
    "communication_channel[skip_confirmation]":1,
}

print()
response = requests.post(createUserURL, headers=canvasAuth, data=payload)

if response.status_code in (200, 201):
    print("  > User created successfully. Confirming...")
    print()
    confirmedUser = fetch_user_info(uin, canvasAPI, canvasToken, accountID)
    display_user_info(confirmedUser)
else:
    print(f"  >>> Error creating user: HTTP {response.status_code} <<<")
    print()
    pprint(response.json())
    print()
