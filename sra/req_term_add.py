#!/usr/bin/python
#
from sqlalchemy import create_engine, text
import sys, argparse, time
from datetime import datetime
from dateutil import parser
from time import strftime
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import logScriptStart
from columnar import columnar
#
envDict = getEnv()
env = 'x'
action = 'x'
termID = 0
eventIDs = [443, 444, 445, 446, 441, 442]
bannerTermsList = []
activeBannerTerm = '999999'
proceed = 'x'
choice = ''
season = ''
seasons = ['0', '1', '5', '8']
dateFormat = "%d-%b-%y"
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

# Create SQLAlchemy engine
connection_string = f"oracle+cx_oracle://{dbUser}:{dbPass}@{dbHost}:{dbPort}/?service_name={dbSid}"
engine = create_engine(connection_string)

with engine.connect() as connection:
    print('')
    print(f"Connected to:  {dbHost}:{dbPort}")
    print('')
    #
    allTermsSql = "SELECT * FROM CORREL.T_TERM"
    allTerms = connection.execute(text(allTermsSql)).fetchall()
    for term in allTerms:
        bannerTermsList.append(term[2])
    #
    activeBannerTerm = input("Enter a valid Banner Term code: ")
    print('')
    if activeBannerTerm in bannerTermsList:
        print(f"The Banner Term {activeBannerTerm} exists. Exiting without changes...")
        print('')
    else:
        termYear = str(activeBannerTerm[1] + activeBannerTerm[2] + activeBannerTerm[3] + activeBannerTerm[4])
        if activeBannerTerm[5] == '0':
            season = "Winter"
        elif activeBannerTerm[5] == '1':
            season = "Spring"
        elif activeBannerTerm[5] == '5':
            season = "Summer"
        elif activeBannerTerm[5] == '8':
            season = "Fall"
        elif activeBannerTerm[5] == '7':
            season = "Academic Year"
        else:
            print(f"Invalid term code {activeBannerTerm}. Exiting without changes...")
            print('')
            sys.exit(1)
        termName = season + " " + str(termYear)
        print(f"Enter the dates for {termName} term: ")
        print('')
        courseStart = parser.parse(input("Enter the Course Start (mm/dd/yy): "))
        courseStart = courseStart.strftime(dateFormat).upper()
        courseEnd = parser.parse(input("Enter the Course End (mm/dd/yy): "))
        courseEnd = courseEnd.strftime(dateFormat).upper()
        print('')
        rosterStart = parser.parse(input("Enter the Roster Start (mm/dd/yy): "))
        rosterStart = rosterStart.strftime(dateFormat).upper()
        rosterEnd = parser.parse(input("Enter the Roster End (mm/dd/yy): "))
        rosterEnd = rosterEnd.strftime(dateFormat).upper()
        print('')
        bannerStart = parser.parse(input("Enter Banner Start (mm/dd/yy): "))
        bannerStart = bannerStart.strftime(dateFormat).upper()
        bannerEnd = parser.parse(input("Enter the Banner End (mm/dd/yy): "))
        bannerEnd = bannerEnd.strftime(dateFormat).upper()
        print('')
        while proceed != 'y' and proceed != 'n':
            print('')
            print("| ========= NEW TERM SUMMARY =========")
            print(f"| Banner Term ID: {activeBannerTerm}")
            print(f"| Term Name:      {termName}")
            print(f"| Course Dates:   {courseStart} to {courseEnd}")
            print(f"| Roster Dates:   {rosterStart} to {rosterEnd}")
            print(f"| Banner Dates:   {bannerStart} to {bannerEnd}")
            print("| ====================================")
            print("")
            proceed = input("Proceed (y/n)? ").strip()[0]
        if proceed == 'y':
            print('')
            try:
                insertSql = f"""insert into CORREL.T_TERM(NAME, BANNER_TERM)values('{termName}', '{activeBannerTerm}')"""
                connection.execute(text(insertSql))
                connection.execute(text("COMMIT"))
                time.sleep(1)
                print(f"> Term {activeBannerTerm} successfully created.")
                print('')
            except:
                input(f"> Term {activeBannerTerm} addition NOT SUCCESSFUL! <enter> to proceed ")
            try:
                viewSql = f"""SELECT TERM_ID FROM CORREL.T_TERM WHERE BANNER_TERM LIKE '{activeBannerTerm}'"""
                activeTermID = connection.execute(text(viewSql)).fetchall()
                activeTermID = [item for term in activeTermID for item in term]
                activeTermID = activeTermID[0]
                print(f"> Term ID (primary key) generated: {activeTermID}")
                print('')
            except:
                input(f"Could not extract new Term ID.")
            try:
                bannerStartDateSql = f"""insert into CORREL.T_TERM_SCHEDULE(TERM_ID, EVENT_ID, \"DATE\") values({activeTermID}, 441, '{bannerStart}')"""
                print(f"> Setting Banner Start Date: {bannerStart}")
                connection.execute(text(bannerStartDateSql))
                bannerEndDateSql =   f"""insert into CORREL.T_TERM_SCHEDULE(TERM_ID, EVENT_ID, \"DATE\") values({activeTermID}, 442, '{bannerEnd}')"""
                print(f"> Setting Banner End Date:   {bannerEnd}")
                connection.execute(text(bannerEndDateSql))
                courseStartDateSql = f"""insert into CORREL.T_TERM_SCHEDULE(TERM_ID, EVENT_ID, \"DATE\") values({activeTermID}, 443, '{courseStart}')"""
                print(f"> Setting Course Start Date: {courseStart}")
                connection.execute(text(courseStartDateSql))
                courseEndDateSql =   f"""insert into CORREL.T_TERM_SCHEDULE(TERM_ID, EVENT_ID, \"DATE\") values({activeTermID}, 444, '{courseEnd}')"""
                print(f"> Setting Course End Date:   {courseEnd}")
                connection.execute(text(courseEndDateSql))
                rosterStartDateSql = f"""insert into CORREL.T_TERM_SCHEDULE(TERM_ID, EVENT_ID, \"DATE\") values({activeTermID}, 445, '{rosterStart}')"""
                print(f"> Setting Roster Start Date: {rosterStart}")
                connection.execute(text(rosterStartDateSql))
                rosterEndDateSql =   f"""insert into CORREL.T_TERM_SCHEDULE(TERM_ID, EVENT_ID, \"DATE\") values({activeTermID}, 446, '{rosterEnd}')"""
                print(f"> Setting Roster End Date:   {rosterEnd}")
                connection.execute(text(rosterEndDateSql))
                print(f"> Committing Changes ")
                print('')
                connection.execute(text("COMMIT"))
                print(f"Term insert for Banner Term {activeBannerTerm} was successful.")
                print('')
            except:
                print(f"Term insert for Banner Term {activeBannerTerm} FAILED!!!")
                print('')
        else:
            print("Exiting without changes...")
            print('')
print('')
