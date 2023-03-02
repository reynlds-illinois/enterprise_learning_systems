import cx_Oracle, sys, argparse, time
from datetime import datetime
from dateutil import parser
from time import strftime
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
from columnar import columnar
#
envDict = getEnv()
env = 'x'
termID = 0
activeBannerTerm = '999999'
dateFormat = "%d-%b-%y"
bannerTermsList = []
termDateIDs = []
newTermDates = []
choice = ''
yesNo = ''
dateStatus = ''
logScriptStart()
print('')
#
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower()[0]
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
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
print('')
print(f"Connected to:  {dbHost}:{dbPort}")
print('')
#
bannerTerm = input("Enter Banner term to edit: ")
print('')
termIDSql = f"""SELECT * FROM CORREL.T_TERM WHERE BANNER_TERM = {bannerTerm}"""
cursor.execute(termIDSql)
r = cursor.fetchall()
termID = r[0][0]
datesSql = f"""SELECT * FROM CORREL.T_TERM_SCHEDULE WHERE TERM_ID = {termID}"""
cursor.execute(datesSql)
time.sleep(1)
termDates = cursor.fetchall()
print(f"|================ {bannerTerm} ================")
print("| ID      DATE          STATUS")
for item in termDates:
    termDateIDs.append(item[0])
    if item[2] == 441: dateStatus = 'Banner Start Date'
    elif item[2] == 442: dateStatus = 'Banner End Date'
    elif item[2] == 443: dateStatus = 'Course Start Date'
    elif item[2] == 444: dateStatus = 'Course End Date'
    elif item[2] == 445: dateStatus = 'Roster Start Date'
    else: dateStatus = 'Roster End Date'
    newTermDates.append([item[0], item[1], item[2], item[3], dateStatus])
    print(f"| {item[0]}     {item[3].strftime(dateFormat).upper()}  <  {dateStatus}")
print("|=========================================")
print('')
#
while choice not in termDateIDs:
    choice = int(input("Please enter the date ID to update: "))
print('')
for line in newTermDates:
    if line[0] == choice:
        #print(line)
        oldDate = str(line[3].strftime(dateFormat).upper())
        newDate = input(f"Please enter the new {line[4]} (mm/dd/yy): ")      # input date string
        newDate = datetime.strptime(newDate, "%m/%d/%y")                     # convert date string to datetime object
        newDate = str(newDate.strftime(dateFormat).upper())                  # convert datetime object back to string with correct format
        print('')
        while yesNo != 'y' and yesNo != 'n':
            yesNo = input(f"Proceed to change {line[4]} from {oldDate} to {newDate} (y/n)? ")
        if yesNo == 'n':
            print("Exiting without changes...")
            cursor.close()
        else:
            print("Applying requested update...")
            dateSql = f"""UPDATE CORREL.T_TERM_SCHEDULE SET \"DATE\" = '{newDate}' WHERE ID = '{choice}'"""
            cursor.execute(dateSql)
            time.sleep(1)
            cursor.execute("COMMIT")
            time.sleep(1)
            cursor.execute(datesSql)
            time.sleep(1)
            termDates = cursor.fetchall()
            print('')
            print(f"|========= UPDATED INFO FOR {bannerTerm} ==========")
            print("| ID      DATE          STATUS")
            for item in termDates:
                termDateIDs.append(item[0])
                if item[2] == 441: dateStatus = 'Banner Start Date'
                elif item[2] == 442: dateStatus = 'Banner End Date'
                elif item[2] == 443: dateStatus = 'Course Start Date'
                elif item[2] == 444: dateStatus = 'Course End Date'
                elif item[2] == 445: dateStatus = 'Roster Start Date'
                else: dateStatus = 'Roster End Date'
                print(f"| {item[0]}     {item[3].strftime(dateFormat).upper()}  <  {dateStatus}")
            print("|==========================================")
            print('')
cursor.close()
