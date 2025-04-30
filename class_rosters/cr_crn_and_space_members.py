#!/usr/bin/python
#
import sys, json
from sqlalchemy import create_engine, text
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import batchLookupReg
from canvasFunctions import bind2Ldap
from canvasFunctions import logScriptStart
#
env = ''
envDict = getEnv()
logScriptStart()
crns = []
lookupChoice = ''
spaceID = []
eXit = 0
choice = ''
crHost = envDict['class.rosters.host']
crXapikey = envDict['class.rosters.xapi']
ldapHost = envDict['UofI.ldap.ad_sys']
ldapBindDn = envDict['UofI.ad_bind']
ldapBindPw = envDict['UofI.ad_bindpwd']
ldapSearchBase = envDict['ad-prod.searchbase_new']
answer = 'x'
print('')
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower()[0]
    if env == 'p':
        dbUser = envDict['req-prod.db.user']
        dbPass = envDict['req-prod.db.pass']
        dbHost = envDict['req-prod.db.sys']
        dbPort = 1521
        dbSid = envDict['req-prod.db.sid']
        envLabel = "PROD"
    else:
        dbUser = envDict['req-stage.db.user']
        dbPass = envDict['req-stage.db.pass']
        dbHost = envDict['req-stage.db.sys']
        dbPort = 1521
        dbSid = envDict['req-stage.db.sid']
        envLabel = "STAGE"
print('')

# Create the SQLAlchemy engine
db_url = f"oracle+cx_oracle://{dbUser}:{dbPass}@{dbHost}:{dbPort}/?service_name={dbSid}"
engine = create_engine(db_url)

ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)
print(f"Connected to:  {dbHost}:{dbPort}")
print('')
while True:
    crns = []
    lookupChoice = ''
    spaceID = []
    eXit = 0
    choice = ''
    #
    print('')
    #
    while lookupChoice != 's' and lookupChoice != 'c':
        lookupChoice = input('Lookup by (s)pace or (c)rn? ').lower()
    if lookupChoice == 's': lookupChoice = 'SPACE'
    else:  lookupChoice = 'CRN'
    print('')
    #
    while eXit == 0:
        if lookupChoice == 'CRN':
            crn = input('Enter CRN: ')
            termcode = input('Enter Banner Term ID: ')
            spaceQuery = text(f"""
                SELECT SR.TARGET_PRODUCT_KEY || TM.BANNER_PART_OF_TERM || '_' || SR.SPACE_ID CID
                FROM CORREL.T_SPACE_ROSTER SRR
                JOIN CORREL.T_SPACE_REQUEST SR ON (SRR.SPACE_ID = SR.SPACE_ID)
                LEFT JOIN CORREL.T_TERM TM ON (SR.TERM_ID = TM.TERM_ID)
                WHERE SRR.TERM_CODE = :termcode
                AND SR.PRODUCT_ID = 'BB9'
                AND SRR.ROSTER_DATA_SOURCE_KEY = :crn
            """)
            with engine.connect() as connection:
                spaceInfo = connection.execute(spaceQuery, {"termcode": termcode, "crn": crn}).fetchall()
            if len(spaceInfo) > 0:
                print(f'Spaces using CRN {crn}: ')
                for item in spaceInfo:
                    print('     ', str(item).strip("',()"))
                    spaceID.append(str(item).strip("',()").split('_')[-1])
                while choice != 'y' and choice != 'n':
                    choice = input('Would you like detailed space and member info? (y/n)').lower()
                if choice == 'n':
                    print('Exiting...')
                    eXit += 1
                    break
            else:
                print(f"No spaces found for CRN {crn}.")
                eXit += 1
                break
        else:
            spaceIDinput = input('Enter space ID: ')
            spaceID.append(spaceIDinput)
        #
        for item in spaceID:
            print(f'========== DETAILED INFO FOR SPACE {item} ==========')
            crnQuery = text(f"""
                SELECT SRR.ROSTER_DATA_SOURCE_KEY CRN,
                       SRR.ROSTER_DATA_SOURCE_KEY CRN,
                       ADR.RUBRIC,
                       ADR.COURSE_NUMBER,
                       ADR.SECTION,
                       ADR.TERM_CODE TERM
                FROM CORREL.T_SPACE_ROSTER SRR
                LEFT JOIN CORREL.T_AD_ROSTER ADR ON (SRR.ROSTER_DATA_SOURCE_KEY = ADR.CRN AND SRR.TERM_CODE = ADR.TERM_CODE)
                WHERE SRR.SPACE_ID = :space_id
            """)
            with engine.connect() as connection:
                crnInfo = connection.execute(crnQuery, {"space_id": item}).fetchall()
            #
            for item in range(0, len(crnInfo)):
                crns.append(crnInfo[item][0])
            termcode = crnInfo[0][5]
            #
            r = batchLookupReg(crHost, crXapikey, termcode, crns)
            print('')
            for c in r:
                print(f"CRN: {c} - term: {termcode}")
                for l in (r[c]):
                    print('    ', l)
                    for uin in r[c][l]:
                        adFilter = '(&(objectclass=user)(uiucEduUIN=' + uin + '))'
                        bitBkt = ldapConn.search(search_base=ldapSearchBase, search_filter=adFilter,
                                                 attributes=['sAMAccountName', 'displayName', 'uiucEduUIN'], size_limit=0)
                        temp = json.loads(ldapConn.response_to_json())
                        netId = temp['entries'][0]['attributes']['sAMAccountName']
                        displayName = temp['entries'][0]['attributes']['displayName']
                        print('        ', netId, '-', displayName)
            print('')
            eXit += 1
    while answer != 'y' and answer != 'n':
        answer = input(f"Continue with another SPACE or CRN in {envLabel} (y/n)? ").strip().lower()
    if answer == 'y':
        print()
        answer = 'x'
        continue
    else:
        print()
        break
#
print('Closing connection and exiting...')
ldapConn.unbind()
print('')
