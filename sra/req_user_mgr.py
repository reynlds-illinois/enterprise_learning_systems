#!/usr/bin/python
#
import os, cx_Oracle, sys, argparse
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
#
envDict = getEnv()
logScriptStart()
env = 'x'
eXit = 0
response = ''
print('')
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower().strip()
if env == 'p':
    dbUser = envDict['req-prod.db.suser']
    dbPass = envDict['req-prod.db.spass']
    dbHost = envDict['req-prod.db.sys']
    dbPort = 1521
    dbSid = envDict['req-prod.db.sid']
    envLabel = "PROD"
else:
    dbUser = envDict['req-stage.db.suser']
    dbPass = envDict['req-stage.db.spass']
    dbHost = envDict['req-stage.db.sys']
    dbPort = 1521
    dbSid = envDict['req-stage.db.sid']
    envLabel = "STAGE"
#
netID = input('Please enter the NetID:  ')
#
try:
    cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
    print(f'Connected to: {dbHost}')
    print('')
except:
    print('Cannot connect to SRA DB at this time')
    eXit += 1
#
while eXit == 0:
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
        if response == 'y':
            delQuery = f"""DELETE FROM CORREL.T_USER_ACCESS_LEVEL ual
                               WHERE ual.USER_ID = '{userInfo[0][0]}'"""
            cursor.execute(delQuery)
            cursor.execute("COMMIT")
            print(f"{netID} has been successfully de-elevated in the SRA {envLabel} Database")
            eXit += 1
        else:
            print('Exiting without changes')
            eXit += 1
    elif len(userInfo) !=0 and userInfo[0][2] is None:      # Non-elevated User Found
        print(f"Username:     {userInfo[0][1]}")
        print(f"Level:        non-Admin")
        print(f"Created Date: {userInfo[0][4]}")
        print('')
        while response != 'y' and response != 'n':
            response = input('Elevate this user account? (y/n)? ').lower().strip()
        if response == 'y':
            elevQuery = f"""INSERT INTO CORREL.T_USER_ACCESS_LEVEL ual
                            (ual.user_id, ual.product_id, ual.access_level_id)
                            VALUES ('{userInfo[0][0]}', 'BB9', 4)"""
            cursor.execute(elevQuery)
            cursor.execute("COMMIT")
            print(f"{netID} has been successefully elevated in the SRA {envLabel} Database")
            eXit += 1
        else:
            print('Exiting without changes')
            eXit += 1
    else:                                                    # User Not Found
        print(f"User {netID} not found in the system.")
        eXit += 1
cursor.close()
print('')
