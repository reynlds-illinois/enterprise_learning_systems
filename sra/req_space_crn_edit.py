import cx_Oracle, sys, argparse
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
from columnar import columnar
#
envDict = getEnv()
env = 'x'
crns = []
crnList = []
crnChange = 'x'
rosterDSK = 'AD'
inputCRN = ''
crnHeader = ['ID', 'Rubric', 'Level', 'Section', 'Term']
logScriptStart()
print('')
#
parser = argparse.ArgumentParser(add_help=True)
parser.add_argument('-s', dest='SPACEID', action='store', help='The globally-unique 6-digit space ID', type=str)
args = parser.parse_args()
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
print('')
print(f"Connected to:  {dbHost}:{dbPort}")
print('')
#
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
#
if not args.SPACEID:
    spaceID = int(input('Please enter the space ID:  '))
else:
    spaceID = int(args.SPACEID)
#
crnInfoQuery = f"""SELECT SRR.ROSTER_DATA_SOURCE_KEY CRN,
       SRR.ROSTER_DATA_SOURCE_KEY CRN,
       ADR.RUBRIC,
       ADR.COURSE_NUMBER,
       ADR.SECTION,
       ADR.TERM_CODE TERM
FROM CORREL.T_SPACE_ROSTER SRR
  LEFT JOIN CORREL.T_AD_ROSTER ADR on(SRR.ROSTER_DATA_SOURCE_KEY = ADR.CRN and SRR.TERM_CODE = ADR.TERM_CODE)
WHERE SRR.SPACE_ID = {spaceID}"""
#
cursor.execute(crnInfoQuery)
crnInfo = cursor.fetchall()
if len(crnInfo) == 0:
    print(f"No CRNs are found for space ID {spaceID}.")
    print('')
else:
    print(f"CRN Info for Space ID: {spaceID}")
    for line in crnInfo:
        crns.append([line[1], line[2], line[3], line[4], line[5]])
        crnList.append(line[1])
    crnTable = columnar(crns, crnHeader, no_borders=True, justify='c', min_column_width=8)
    print(crnTable)
    print('')
#
while crnChange != 'a' and crnChange != 'r' and crnChange != 'q':
    crnChange = input(f"Would you like to (a)dd or (r)emove a CRN from space ID {spaceID}: ").lower()[0]
print('')
if crnChange == 'q':
    print("Exiting without changes...")
    #break
elif crnChange == 'r':
    remChoice = 'x'
    while inputCRN not in crnList:
        inputCRN = input("Enter CRN from the above table: ")
    termID = input("Enter Banner Term ID: ")
    print('')
    remChoice = input(f"Remove CRN {inputCRN} from space ID {spaceID} for term {termID} (y/n)? ")
    if remChoice == 'n':
        print("Exiting without changes...")
        #break
    else:
        print("Removing CRN...")
        remSql = f"""DELETE FROM correl.t_space_roster tsr
                     WHERE tsr.roster_data_source_key = {inputCRN}
                         AND tsr.space_id = {spaceID}
                         AND tsr.term_code = {termID}"""
        cursor.execute(remSql)
        cursor.execute("COMMIT")
        print("CRN Removed and Committed...")
        cursor.execute(crnInfoQuery)
        crnInfo = cursor.fetchall()
        print(f"Updated CRN Info for Space ID: {spaceID}")
        crns = []
        for line in crnInfo:
            crns.append([line[1], line[2], line[3], line[4], line[5]])
        crnTable = columnar(crns, crnHeader, no_borders=True, justify='c', min_column_width=8)
        print(crnTable)
        print('')
else:
    newCRN = input("Enter the CRN to add to the space: ")
    if newCRN in crnList:
        print("That CRN is already part of this course space. Exiting...")
        print('')
    else:
        termID = int(input("Enter the Banner Term ID for this CRN: "))
        print('')
        addChoice = input(f"Add ID {newCRN} to space ID {spaceID} for term {termID} (y/n)?")
        if addChoice == 'n':
            print("Exiting without changes...")
            #break
        else:
            print("Writing changes...")
            addSql = f"""INSERT into correl.t_space_roster tsr
                        (tsr.space_id, tsr.roster_data_source_key,
                        tsr.roster_data_source_id, tsr.term_code)
                        values({spaceID}, {newCRN}, '{rosterDSK}', {termID})"""
            print('')
            print(addSql)
            print('')
            cursor.execute(addSql)
            cursor.execute("COMMIT")
            print("CRN Successfully added to Space and committed")
            cursor.execute(crnInfoQuery)
            crnInfo = cursor.fetchall()
            print(f"Updated CRN Info for Space ID: {spaceID}")
            crns = []
            for line in crnInfo:
                crns.append([line[1], line[2], line[3], line[4], line[5]])
            crnTable = columnar(crns, crnHeader, no_borders=True, justify='c', min_column_width=8)
            print(crnTable)
            print('')
print('')
