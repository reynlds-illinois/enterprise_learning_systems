import cx_Oracle, sys, json
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
from canvasFunctions import bind2Ldap
from pprint import pprint
from columnar import columnar
#
envDict = getEnv()
logScriptStart()
print('')
#
dbUser = envDict['req-prod.db.user']
dbPass = envDict['req-prod.db.pass']
dbHost = envDict['req-prod.db.sys']
dbPort = 1521
dbSid = envDict['req-prod.db.sid']
ldapHost = envDict['UofI.ldap.ad_sys']
ldapBindDn = envDict['UofI.ad_bind']
ldapBindPw = envDict['UofI.ad_bindpwd']
ldapRosterSearchBase = "OU=Class Rosters,OU=Register,OU=Urbana,DC=ad,DC=uillinois,DC=edu"
ldapUserSearchBase = "OU=Urbana,DC=ad,DC=uillinois,DC=edu"
adGroups = {}
adUsers = []
response = 'x'
eXit = 0
crnInfo = []
spaceInfo = []
memberData = []
crnData = []
adGroupFilter = ''
#
print('')
while eXit == 0:
    try:
        cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
    except:
        print("Cannot connect to SRA Database...exiting...")
        eXit += 1
    while response != 's' and response != 'c':
        response = input("Lookup by (s)pace or (c)rn? ").lower().strip()
    print('')
    #
    if response == 's':
        spaceID = input("Please enter the Space ID: ")
        crnQuery = f"""select SRR.ROSTER_DATA_SOURCE_KEY CRN,
                         SRR.TERM_CODE
                         from CORREL.T_SPACE_ROSTER SRR
                         where SRR.SPACE_ID = {spaceID}"""
        cursor.execute(crnQuery)
        crnInfo = cursor.fetchall()
    else:
        crnTemp = input("Please enter the CRN: ")
        termTemp = input("Plese enter the Banner Term ID: ")
        crnInfo.append([crnTemp, termTemp])
        spaceQuery = f"""select SR.TARGET_PRODUCT_KEY || TM.BANNER_PART_OF_TERM || '_' || SR.SPACE_ID CID
                         from CORREL.T_SPACE_ROSTER SRR
                         join CORREL.T_SPACE_REQUEST SR on(SRR.SPACE_ID = SR.SPACE_ID)
                         left join CORREL.T_TERM TM on(SR.TERM_ID = TM.TERM_ID)
                         where SRR.TERM_CODE = {termTemp} and SR.PRODUCT_ID = 'BB9'
                         and SRR.ROSTER_DATA_SOURCE_KEY = {crnTemp}"""
        cursor.execute(spaceQuery)
        spaceInfo = cursor.fetchall()
        print(spaceInfo, type(spaceInfo))
        print("|-----------------------------------------------------------")
        print(f"| Space(s) associated with CRN {crnTemp} in Term {termTemp}")
        print("|")
        for space in spaceInfo:
            print(f"|     {space}")
        print("|-----------------------------------------------------------")
    #
    print('')
    try:
        ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)
        print("Connected to Active Directory")
    except:
        print("Cannot connect to Active Directory")
        eXit += 1
    print('')
    for crn in crnInfo:
        adGroupFilter = f"(&(uiucEduRosterTermCode={crn[1]})(uiucEduRosterCRN={crn[0]}))"
        adGroupQuery = ldapConn.search(search_base=ldapRosterSearchBase, search_filter=adGroupFilter,
            attributes = ['uiucEduRosterCourseSubjectCode',
                          'uiucEduRosterCourseNumber',
                          'uiucEduRosterSectionNumber',
                          'uiucEduRosterTermCode',
                          'uiucEduRosterCRN',
                          'uiucEduRosterSectionGradeable',
                          'uiucEduRosterCrossListControllingDepartmentCode',
                          'uiucEduRosterStaff',
                          'uiucEduRosterUndergraduateStudents',
                          'uiucEduRosterGraduateStudents'],
                           size_limit=0)
        if adGroupQuery == True:
            adGroups = json.loads(ldapConn.response_to_json())
            courseSubject = str(adGroups['entries'][0]['attributes']['uiucEduRosterCourseSubjectCode'])
            courseNumber = str(adGroups['entries'][0]['attributes']['uiucEduRosterCourseNumber'])
            courseSection = str(adGroups['entries'][0]['attributes']['uiucEduRosterSectionNumber'])
            courseTerm = str(adGroups['entries'][0]['attributes']['uiucEduRosterTermCode'])
            sectionID = f"{courseSubject}_{courseNumber}_{courseSection}"
            enrollTypes = ['uiucEduRosterStaff', 'uiucEduRosterGraduateStudents', 'uiucEduRosterUndergraduateStudents']
            crnData.append([crn[0], crn[1], courseSubject, courseNumber, courseSection, sectionID])
            for role in enrollTypes:
                if role == "uiucEduRosterStaff":
                    level = "S"
                elif role == "uiucEduRosterGraduateStudents":
                    level = "G"
                elif role == "uiucEduRosterUndergdraduateStudents":
                    level = "U"
                for item in adGroups['entries'][0]['attributes'][role]:
                    netID = item.replace('CN=', '').split(",",1)[0]
                    memberData.append([netID, sectionID, level, crn[0], courseTerm])
        else:
            print(f"CRN {crn[0]} and Term ID {termTemp} are not found in Active Directory.")
            eXit += 1
    crnHeader = ['CRN', 'TERM', 'RUBRIC', 'NUMBER', 'SECTION', 'SECTION_ID']
    memberHeader = ['NETID', 'SECTION_ID', 'LEVEL', 'TERM', 'CRN']
    crnTable = columnar(crnData, crnHeader, no_borders=True)
    memberTable = columnar(memberData, memberHeader, no_borders=True)
    print(crnTable)
    print('')
    print(memberTable)
    print('')
    eXit += 1
print('')
