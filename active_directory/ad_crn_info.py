import sys, argparse, json
from pprint import pprint
from sqlalchemy import text
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
from canvasFunctions import bind2Ldap

# Initialize environment and log script start
envDict = getEnv()
logScriptStart()
print('')

# LDAP connection setup
ldapHost = envDict['UofI.ldap.ad_sys']
ldapBindDn = envDict['UofI.ad_bind']
ldapBindPw = envDict['UofI.ad_bindpwd']
ldapRosterSearchBase = "OU=Class Rosters,OU=Register,OU=Urbana,DC=ad,DC=uillinois,DC=edu"
ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)

# Prompt for CRN and Term
crn = input("Enter CRN to search:    ")
term = input("Enter Banner Term Code: ")
print('')

# LDAP query
adGroupFilter = f"(&(uiucEduRosterTermCode={term})(uiucEduRosterCRN={crn}))"
adGroupQuery = ldapConn.search(
    search_base=ldapRosterSearchBase,
    search_filter=adGroupFilter,
    attributes=[
        'uiucEduRosterCourseSubjectCode',
        'uiucEduRosterCourseNumber',
        'uiucEduRosterSectionNumber',
        'uiucEduRosterTermCode',
        'uiucEduRosterCRN',
        'uiucEduRosterSectionGradeable',
        'uiucEduRosterCrossListControllingDepartmentCode',
        'uiucEduRosterStaff',
        'uiucEduRosterUndergraduateStudents',
        'uiucEduRosterGraduateStudents',
        'uiucEduRosterDepartmentCode'
    ],
    size_limit=0
)
adGroup = json.loads(ldapConn.response_to_json())

# Extract course details from LDAP response
courseSubject = str(adGroup['entries'][0]['attributes']['uiucEduRosterCourseSubjectCode'])
courseNumber = str(adGroup['entries'][0]['attributes']['uiucEduRosterCourseNumber'])
courseSection = str(adGroup['entries'][0]['attributes']['uiucEduRosterSectionNumber'])
courseTerm = str(adGroup['entries'][0]['attributes']['uiucEduRosterTermCode'])
courseDeptCode = str(adGroup['entries'][0]['attributes']['uiucEduRosterDepartmentCode'])
courseGradeable = str(adGroup['entries'][0]['attributes']['uiucEduRosterSectionGradeable'])

# Print course details
print("|-----------------------------------")
print(f"| CRN:        {crn}")
print(f"| Term:       {courseTerm}")
print(f"| Rubric:     {courseSubject}")
print(f"| Number:     {courseNumber}")
print(f"| Section:    {courseSection}")
print(f"| Dept Code:  {courseDeptCode}")
print(f"| Gradeable:  {courseGradeable}")
print("|-----------------------------------")
print('')

# SQLAlchemy connection setup
dbUser = envDict['req-prod.db.suser']
dbPass = envDict['req-prod.db.spass']
dbHost = envDict['req-prod.db.sys']
dbPort = 1521
dbSid = envDict['req-prod.db.sid']

# Connect to the database using connect2Sql
connection = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)

# Example SQL query (replace with actual query as needed)
if connection:
    try:
        sql_query = text("SELECT * FROM some_table WHERE crn = :crn AND term = :term")
        result = connection.execute(sql_query, {"crn": crn, "term": term})
        for row in result:
            pprint(row)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
    finally:
        connection.close()
