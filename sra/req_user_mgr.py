#!/usr/bin/python
#
import os, sys, argparse
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
logScriptStart()
#
realm = realm()
dbUser = realm['sraDbUser']
dbPass = realm['sraDbPass']
dbHost = realm['sraDbHost']
dbPort = realm['sraDbPort']
dbSid = realm['sraDbSid']
envLabel = realm['envLabel']
print()
print(f"Connected to:  {envLabel}")
eXit = 0
response = 'x'
answer = 'x'
print('')
#
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
print(f'Connected to: {dbHost}')
print('')
#    envLabel = "STAGE"
while True:
    #
    netID = input('Please enter the NetID:  ')
    #
    while True:
        userQuery = f"""select u.user_id "USER_ID",
                u.LOGIN "NETID",
                ual.ACCESS_LEVEL_ID "ACCESS_LEVEL_ID",
                al.ACCESS_LEVEL_DESC "LEVEL_DESC",
                TO_CHAR(u.CREATE_DATE, 'YYYY/MM/DD') "CREATE_DATE"
            from CORREL.t_user u
                LEFT JOIN CORREL.T_USER_ACCESS_LEVEL ual on(u.user_id = ual.USER_ID)
                LEFT JOIN CORREL.t_access_level al on(al.code = ual.ACCESS_LEVEL_ID)
                where u.LOGIN = '{netID}'"""
        #
        cursor.execute(userQuery)
        userInfo = cursor.fetchall()
        #
        if len(userInfo) != 0 and userInfo[0][2] == 4:          # Elevated User Found
            print(f"Username:     {userInfo[0][1]}")
            print(f"Level:        {userInfo[0][3]}")
            print(f"Created Date: {userInfo[0][4]}")
            print('')
            while response != 'y' and response != 'n':
                response = input('De-Elevate this user account? (y/n)? ').lower().strip()
                print()
            if response == 'y':
                delQuery = f"""DELETE FROM CORREL.T_USER_ACCESS_LEVEL ual
                                   WHERE ual.USER_ID = '{userInfo[0][0]}'"""
                cursor.execute(delQuery)
                cursor.execute("COMMIT")
                print()
                print(f"> {netID} has been successfully de-elevated in the SRA {envLabel} Database")
                print()
                response = 'x'
                break
            else:
                print('Exiting without changes')
                response = 'x'
                break
        elif len(userInfo) !=0 and userInfo[0][2] is None:                    # Non-elevated User Found
            print(f"Username:     {userInfo[0][1]}")
            print(f"Level:        non-Admin")
            print(f"Created Date: {userInfo[0][4]}")
            print('')
            while response != 'y' and response != 'n':
                response = input('Elevate this user account? (y/n)? ').lower().strip()
                print()
            if response == 'y':
                elevQuery = f"""INSERT INTO CORREL.T_USER_ACCESS_LEVEL ual
                                (ual.user_id, ual.product_id, ual.access_level_id)
                                VALUES ('{userInfo[0][0]}', 'BB9', 4)"""
                cursor.execute(elevQuery)
                cursor.execute("COMMIT")
                print()
                print(f"> {netID} has been successefully elevated in the SRA {envLabel} Database")
                print()
                response = 'x'
                break
            else:
                print('Exiting without changes')
                response = 'x'
                break
        else:                                                                 # User Not Found
            print(f"User {netID} not found in the system.")
            break
    while answer != 'y' and answer != 'n':
        answer = input(f"Continue with another user in {envLabel} (y/n)? ").strip().lower()
    if answer == 'y':
        print()
        answer = 'x'
        continue
    else:
        print()
        break
#
print('Closing connection and exiting...')
cursor.close()
print('')
