#!/usr/bin/python
#
import sys, os, requests, json
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm

realm = realm()
canvasAPI = realm['canvasApi']
canvasToken = realm['canvasToken']
canvasAuth = {"Authorization": f"Bearer {canvasToken}"}
accountID = "1"

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
    user = response.json()
    print("  > User created successfully.")
    print()
    print(f"    Canvas ID:      {user.get('id')}")
    print(f"    Name:           {user.get('name')}")
    print(f"    Login ID:       {user.get('login_id')}")
    print(f"    SIS ID:         {user.get('sis_user_id')}")
    print(f"    Integration ID: {user.get('integration_id')}")
    print()
else:
    print(f"  >>> Error creating user: HTTP {response.status_code} <<<")
    print()
    pprint(response.json())
    print()
