#!/usr/bin/python
#
import sys, time
from sqlalchemy import create_engine, text
from datetime import datetime
from dateutil import parser
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

# Function to add a new term
def add_term(connection):
    proceed = ''
    print("Adding a New Term")
    print()
    activeBannerTerm = input("  > Enter the Banner term (e.g., 120251): ").strip()
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
        print(f"  = Invalid term code {activeBannerTerm}. Exiting without changes...")
        print('')
        sys.exit(1)
    termName = season + " " + str(termYear)
    print()
    print(f"  ### Adding {termName} term")
    print()
    #print(f"Enter the dates for {termName} term: ")
    #print('')
    #
    courseStart = parser.parse(input("  > Enter the Course Start (mm/dd/yy): "))
    courseStart = courseStart.strftime(dateFormat).upper()
    courseEnd = parser.parse(input("  > Enter the Course End (mm/dd/yy): "))
    courseEnd = courseEnd.strftime(dateFormat).upper()
    print('')
    rosterStart = parser.parse(input("  > Enter the Roster Start (mm/dd/yy): "))
    rosterStart = rosterStart.strftime(dateFormat).upper()
    rosterEnd = parser.parse(input("  > Enter the Roster End (mm/dd/yy): "))
    rosterEnd = rosterEnd.strftime(dateFormat).upper()
    print('')
    bannerStart = parser.parse(input("  > Enter Banner Start (mm/dd/yy): "))
    bannerStart = bannerStart.strftime(dateFormat).upper()
    bannerEnd = parser.parse(input("  > Enter the Banner End (mm/dd/yy): "))
    bannerEnd = bannerEnd.strftime(dateFormat).upper()
    print('')
    while proceed != 'y' and proceed != 'n':
        print('')
        print("  | ========= NEW TERM SUMMARY =========")
        print(f"  | Banner Term ID: {activeBannerTerm}")
        print(f"  | Term Name:      {termName}")
        print(f"  | Course Dates:   {courseStart} to {courseEnd}")
        print(f"  | Roster Dates:   {rosterStart} to {rosterEnd}")
        print(f"  | Banner Dates:   {bannerStart} to {bannerEnd}")
        print("  | ====================================")
        print("")
        proceed = input("  ### Proceed (y/n)? ").strip()[0]
    if proceed == 'y':
        try:
            print('')
            insertSql = f"""insert into CORREL.T_TERM(NAME, BANNER_TERM)values('{termName}', '{activeBannerTerm}')"""
            connection.execute(text(insertSql))
            connection.execute(text("COMMIT"))
            time.sleep(1)
            print(f"> Term {activeBannerTerm} successfully created.")
            print('')
        except Exception as E:
            print(f"> Error: {E}")
            print()
        try:
            viewSql = f"""SELECT TERM_ID FROM CORREL.T_TERM WHERE BANNER_TERM LIKE '{activeBannerTerm}'"""
            activeTermID = connection.execute(text(viewSql)).fetchall()
            activeTermID = [item for term in activeTermID for item in term]
            activeTermID = activeTermID[0]
            print(f"> Term ID (primary key) generated: {activeTermID}")
            print('')
        except:
            input(f"> Could not extract new Term ID.")
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
            print(f">>> Term insert for Banner Term {activeBannerTerm} was successful. <<<")
            print('')
        except:
            print(f"### Term insert for Banner Term {activeBannerTerm} FAILED!!! ###")
            print('')
    else:
        print("Exiting without changes...")
        print('')
        sys.exit(1)
#
# Function to edit an existing term
def edit_term(connection):
    choice = ''
    print("Edit an Existing Term")
    bannerTerm = input("  > Enter Banner term to edit: ").strip()

    # Fetch term ID
    termIDSql = text("SELECT * FROM CORREL.T_TERM WHERE BANNER_TERM = :bannerTerm")
    result = connection.execute(termIDSql, {"bannerTerm": bannerTerm}).fetchall()
    if not result:
        print(f"  # No term found for Banner term '{bannerTerm}'.")
        return
    termID = result[0][0]

    # Fetch term dates
    datesSql = text("SELECT * FROM CORREL.T_TERM_SCHEDULE WHERE TERM_ID = :termID")
    termDates = connection.execute(datesSql, {"termID": termID}).fetchall()
    sleep(1)

    print(f"  |================ {bannerTerm} ================")
    print("  | ID      DATE          STATUS")
    for item in termDates:
        termDateIDs.append(item[0])
        if item[2] == 441: dateStatus = 'Banner Start Date'
        elif item[2] == 442: dateStatus = 'Banner End Date'
        elif item[2] == 443: dateStatus = 'Course Start Date'
        elif item[2] == 444: dateStatus = 'Course End Date'
        elif item[2] == 445: dateStatus = 'Roster Start Date'
        else: dateStatus = 'Roster End Date'
        newTermDates.append([item[0], item[1], item[2], item[3], dateStatus])
        print(f"  | {item[0]}     {item[3].strftime(dateFormat).upper()}  <  {dateStatus}")
    print("  |=========================================")
    print('')

    # Prompt for date ID to update
    while choice not in termDateIDs:
        choice = int(input("  > Please enter the date ID to update: "))
    print('')

    for line in newTermDates:
        if line[0] == choice:
            oldDate = str(line[3].strftime(dateFormat).upper())
            newDate = input(f"  > Please enter the new {line[4]} (mm/dd/yy): ").strip()
            newDate = datetime.strptime(newDate, "%m/%d/%y").strftime(dateFormat).upper()
            print('')
            yesNo = ''
            while yesNo not in ['y', 'n']:
                yesNo = input(f"  # Proceed to change {line[4]} from {oldDate} to {newDate} (y/n)? ").lower()
            if yesNo == 'n':
                print("  # Exiting without changes...")
                break
            else:
                print("  # Applying requested update...")
                dateSql = text("UPDATE CORREL.T_TERM_SCHEDULE SET \"DATE\" = :newDate WHERE ID = :choice")
                connection.execute(dateSql, {"newDate": newDate, "choice": choice})
                connection.execute(text("COMMIT"))
                sleep(1)

                # Fetch updated term dates
                termDates = connection.execute(datesSql, {"termID": termID}).fetchall()
                sleep(1)
                print('')
                print(f"  |========= UPDATED INFO FOR {bannerTerm} ==========")
                print("  | ID      DATE          STATUS")
                for item in termDates:
                    if item[2] == 441: dateStatus = 'Banner Start Date'
                    elif item[2] == 442: dateStatus = 'Banner End Date'
                    elif item[2] == 443: dateStatus = 'Course Start Date'
                    elif item[2] == 444: dateStatus = 'Course End Date'
                    elif item[2] == 445: dateStatus = 'Roster Start Date'
                    else: dateStatus = 'Roster End Date'
                    print(f"  | {item[0]}     {item[3].strftime(dateFormat).upper()}  <  {dateStatus}")
                print("  |==========================================")
                print('')
#
# Main function
def main():
    with engine.connect() as connection:
        print()
        action = input("Choose one:  (a)dd or (e)dit a term: ").lower().strip()
        print()
        if action == 'a': add_term(connection)
        elif action == 'e': edit_term(connection)
        else: print("Invalid choice. Exiting...")
        print()
#
if __name__ == "__main__":
    main()
