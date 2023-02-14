import cx_Oracle, sys, argparse, json
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
from canvasFunctions import bind2Ldap
from pprint import pprint
#
envDict = getEnv()
logScriptStart()
print('')
#
parser = argparse.ArgumentParser(add_help=True)
parser.add_argument('-s', dest='SPACEID', action='store', help='The globally-unique 6-digit space ID', type=str)
args = parser.parse_args()
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
#
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
#
if not args.SPACEID:
    spaceID = input('Please enter the space ID:  ')
else:
    spaceID = args.SPACEID
print('')
spaceQuery = f"""select SRR.ROSTER_DATA_SOURCE_KEY CRN,
                 SRR.TERM_CODE
                 from CORREL.T_SPACE_ROSTER SRR
                 where SRR.SPACE_ID = {spaceID}"""
#
cursor.execute(spaceQuery)
crnInfo = cursor.fetchall()
#
ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)
#
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
    adGroups = json.loads(ldapConn.response_to_json())
    courseSubject = str(adGroups['entries'][0]['attributes']['uiucEduRosterCourseSubjectCode'])
    courseNumber = str(adGroups['entries'][0]['attributes']['uiucEduRosterCourseNumber'])
    courseSection = str(adGroups['entries'][0]['attributes']['uiucEduRosterSectionNumber'])
    courseTerm = str(adGroups['entries'][0]['attributes']['uiucEduRosterTermCode'])
    print(F"CRN: {crn[0]} | {courseSubject} {courseNumber} {courseSection} {courseTerm}")
    print("   * Staff")
    for item in adGroups['entries'][0]['attributes']['uiucEduRosterStaff']:
        print("       -",item.replace('CN=', '').split(",",1)[0])
    print("   * Graduate Students")
    for item in adGroups['entries'][0]['attributes']['uiucEduRosterGraduateStudents']:
        print("       -",item.replace('CN=', '').split(",",1)[0])
    print("   * Undergraduate Students")
    for item in adGroups['entries'][0]['attributes']['uiucEduRosterUndergraduateStudents']:
        print("       -",item.replace('CN=', '').split(",",1)[0])
print('')
