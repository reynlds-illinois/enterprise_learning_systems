import os, time, cx_Oracle, urllib, sys, json, requests, argparse
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
#from canvasFunctions import crnLookup
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
crHost = envDict['class.rosters.host']
crXapikey = envDict['class.rosters.xapi']
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
print(f"> Connected to:  {dbHost}:{dbPort}")
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
    print(f"> No CRNs are found for space ID {spaceID}.")
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
    crnChange = input(f"Would you like to (a)dd or (r)emove a CRN from space ID {spaceID} or (q)uit: ").lower()[0]
print('')
if crnChange == 'q':
    print("> Exiting without changes...")
    #break
elif crnChange == 'r':
    remChoice = 'x'
    while inputCRN not in crnList:
        inputCRN = input("Enter CRN from the above table: ")
    termID = input("Enter Banner Term ID: ")
    print('')
    remChoice = input(f"Remove CRN {inputCRN} from space ID {spaceID} for term {termID} (y/n)? ").lower()[0]
    if remChoice == 'n':
        print("> Exiting without changes...")
        #break
    else:
        print("Removing CRN...")
        remSqlTSR = f"""DELETE FROM correl.t_space_roster tsr
                        WHERE tsr.roster_data_source_key = {inputCRN}
                            AND tsr.space_id = {spaceID}
                            AND tsr.term_code = {termID}"""
        cursor.execute(remSqlTSR)
        cursor.execute("COMMIT")
        print("> CRN Removed and Committed...")
        cursor.execute(crnInfoQuery)
        crnInfo = cursor.fetchall()
        print(f"> Updated CRN Info for Space ID: {spaceID}")
        crns = []
        for line in crnInfo:
            crns.append([line[1], line[2], line[3], line[4], line[5]])
        crnTable = columnar(crns, crnHeader, no_borders=True, justify='c', min_column_width=8)
        print(crnTable)
        print('')
else:
    newCRN = input("Enter the CRN to add to the space: ")
    if newCRN in crnList:
        print("> That CRN is already part of this course space. Exiting...")
        print('')
    else:
        termID = int(input("Enter the Banner Term ID for this CRN: "))
        apiEndpoint = f"v1.0/section-lookup/{termID}/{newCRN}"
        crnUrl = urllib.parse.urljoin(crHost, apiEndpoint)
        headers = {"X-API-KEY": crXapikey}
        r = requests.get(crnUrl, headers=headers)
        if r.status_code != 200:
            print('')
            print(f"> The CRN {newCRN} in Term {termID} is not found in Class Rosters.")
            print('')
        else:
            r = r.json()
            crn = r['crn']
            rubric = r['crs_subj_cd'].upper()
            level = r['crs_nbr']
            section = r['sect_nbr'].upper()
            term = r['term_cd']
            controllingDept = r['dept_cd']
            print('')
            addChoice = input(f"Add CRN {newCRN} to space ID {spaceID} for term {termID} (y/n)? ").lower()[0]
            if addChoice == 'n':
                print("> Exiting without changes...")
                #break
            else:
                print("> Writing changes...")
                # T_SPACE_ROSTER Table
                addSqlTSR = f"""INSERT into correl.t_space_roster tsr
                            (tsr.space_id, tsr.roster_data_source_key,
                             tsr.roster_data_source_id, tsr.term_code)
                             values({spaceID}, {newCRN}, '{rosterDSK}', {termID})"""
                cursor.execute(addSqlTSR)
                cursor.execute("COMMIT")
                time.sleep(1)
                # T_AD_ROSTER Table
                readTARSql = f"""SELECT * FROM correl.t_ad_roster
                                 WHERE term_code = {termID} and crn = {newCRN}"""
                cursor.execute(readTARSql)
                crnCheck = cursor.fetchall()
                if len(crnCheck) == 0:
                    addSqlTAR = f"""INSERT INTO correl.t_ad_roster tar
                                (tar.controlling_dept_key, tar.rubric, tar.course_number,
                                 tar.section, tar.crn, tar.term_code)
                                 values('{controllingDept}', '{rubric}', '{level}', '{section}', '{crn}', '{term}')"""
                    cursor.execute(addSqlTAR)
                    cursor.execute("COMMIT")
                print("> CRN Successfully added to Space and committed")
                cursor.execute(crnInfoQuery)
                crnInfo = cursor.fetchall()
                print(f"> Updated CRN Info for Space ID: {spaceID}")
                crns = []
                for line in crnInfo:
                    crns.append([line[1], line[2], line[3], line[4], line[5]])
                crnTable = columnar(crns, crnHeader, no_borders=True, justify='c', min_column_width=8)
                print(crnTable)
                print('')
cursor.close()
print('')
