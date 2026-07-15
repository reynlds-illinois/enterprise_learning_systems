#!/usr/bin/python
#
import sys, requests
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm, logScriptStart, getEnv, canvasGetUserInfoLive
logScriptStart()
realm = realm()
env = getEnv()
canvasAPI = realm['canvasApi']
canvasToken = realm['canvasToken']
answer = ''
accountID = '1'
#params = {"per_page": 100}
canvasAuth = {"Authorization": f"Bearer {canvasToken}"}
#
while answer != 'y' and answer != 'n' and answer != 'q':
    myAction = input("  > Action to perform on user: create (n)ew; get (i)nfo ").strip().lower()
    print()
    if myAction == 'q':
        print(f'>>> Exiting and closing connection to {canvasAPI}')
        print()
        sys.exit(0)
    if myAction == 'i':
        searchTerm = input("  > Enter NetID, UIN or Canvas ID to search:  ").lower()
        print()
        canvasGetUserInfoLive(searchTerm, canvasAPI, canvasAuth)
    if myAction == 'n':
        myResponse = ''
        firstname = input("  > Enter user's first name: ")
        print()
        lastname = input("  > Enter user's last name: ")
        print()
        netid = input("  > Enter user's NetID: ").lower()
        print()
        uin = input("  > Enter user's UIN: ").lower()
        print()
        email = input("  > Enter user's email: ").strip()
        fullname = f"{firstname} {lastname}"
        sortableName = f"{lastname}, {firstname}"
        while myResponse != 'y' and myResponse != 'n':
            print()
            print("  > Confirm user information:")
            print(f"  > First Name:    {firstname}")
            print(f"  > Last Name:     {lastname}")
            print(f"  > Full Name:     {fullname}")
            print(f"  > Sortable Name: {sortableName}")
            print(f"  > NetID:         {netid}")
            print(f"  > UIN:           {uin}")
            print(f"  > Email:         {email}")
            print()
            myResponse = input("  > Is this information correct (y/n)? ").strip().lower()
            if myResponse == 'n':
                print()
                print("  > User creation aborted. Please re-run the script to try again.")
                print()
                break
            else:
                print()
                print("  > Proceeding with user creation...")
                print()
                #
                createUserURL = f"{canvasAPI}accounts/{accountID}/users"
                #
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
                #
                if response.status_code in (200, 201):
                    print("  > User created successfully. Confirming...")
                    print()
                    canvasGetUserInfoLive(uin,canvasAPI, canvasAuth)
                else:
                    print(f"  >>> Error creating user: HTTP {response.status_code} <<<")
                    print()
                    pprint(response.json())
                    print()
        #
    answer = input("Continue with another user action (y/n)? ").strip().lower()
    if answer == 'y':
        print()
        answer = ''
        continue
    else:
        print()
        break
print(f'Exiting and closing connection to {canvasAPI}')
print()