#!/usr/bin/python
#
import sys
from sqlalchemy import create_engine, text
from datetime import datetime
from time import sleep
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv, logScriptStart

# Initialize environment variables
envDict = getEnv()
env = 'x'
dateFormat = "%d-%b-%y"
termDateIDs = []
newTermDates = []
choice = ''
yesNo = ''
dateStatus = ''
logScriptStart()
print('')

# Prompt for environment selection
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

# Create SQLAlchemy engine
connection_string = f"oracle+cx_oracle://{dbUser}:{dbPass}@{dbHost}:{dbPort}/?service_name={dbSid}"
engine = create_engine(connection_string)

with engine.connect() as connection:
    print('')
    print(f"Connected to:  {dbHost}:{dbPort}")
    print('')

    # Prompt for Banner term
    bannerTerm = input("Enter Banner term to edit: ")
    print('')

    # Fetch term ID
    termIDSql = text(f"SELECT * FROM CORREL.T_TERM WHERE BANNER_TERM = :bannerTerm")
    result = connection.execute(termIDSql, {"bannerTerm": bannerTerm}).fetchall()
    termID = result[0][0]

    # Fetch term dates
    datesSql = text(f"SELECT * FROM CORREL.T_TERM_SCHEDULE WHERE TERM_ID = :termID")
    termDates = connection.execute(datesSql, {"termID": termID}).fetchall()
    sleep(1)

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

    # Prompt for date ID to update
    while choice not in termDateIDs:
        choice = int(input("Please enter the date ID to update: "))
    print('')

    for line in newTermDates:
        if line[0] == choice:
            oldDate = str(line[3].strftime(dateFormat).upper())
            newDate = input(f"Please enter the new {line[4]} (mm/dd/yy): ")  # input date string
            newDate = datetime.strptime(newDate, "%m/%d/%y")                 # convert date string to datetime object
            newDate = str(newDate.strftime(dateFormat).upper())              # convert datetime object back to string with correct format
            print('')
            while yesNo != 'y' and yesNo != 'n':
                yesNo = input(f"Proceed to change {line[4]} from {oldDate} to {newDate} (y/n)? ")
            if yesNo == 'n':
                print("Exiting without changes...")
                break
            else:
                print("Applying requested update...")
                dateSql = text(f"UPDATE CORREL.T_TERM_SCHEDULE SET \"DATE\" = :newDate WHERE ID = :choice")
                connection.execute(dateSql, {"newDate": newDate, "choice": choice})
                connection.execute(text("COMMIT"))
                sleep(1)

                # Fetch updated term dates
                termDates = connection.execute(datesSql, {"termID": termID}).fetchall()
                sleep(1)
                print('')
                print(f"|========= UPDATED INFO FOR {bannerTerm} ==========")
                print("| ID      DATE          STATUS")
                for item in termDates:
                    if item[2] == 441: dateStatus = 'Banner Start Date'
                    elif item[2] == 442: dateStatus = 'Banner End Date'
                    elif item[2] == 443: dateStatus = 'Course Start Date'
                    elif item[2] == 444: dateStatus = 'Course End Date'
                    elif item[2] == 445: dateStatus = 'Roster Start Date'
                    else: dateStatus = 'Roster End Date'
                    print(f"| {item[0]}     {item[3].strftime(dateFormat).upper()}  <  {dateStatus}")
                print("|==========================================")
                print('')
