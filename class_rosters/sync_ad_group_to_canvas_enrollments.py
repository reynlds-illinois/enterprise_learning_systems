#!/usr/bin/python
#
import sys, requests
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from columnar import columnar
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import realm
#
env = getEnv()
#
# this will be the Canvas API base URL
canvasAPI = 'https://illinoisedu.beta.instructure.com/api/v1'
# this is a user token with sufficient privileges to manage course enrollments
canvasToken = env['canvas.token']
# this is a mashup for use with requests library headers
canvasAuth = {"Authorization": f"Bearer {canvasToken}"}
# this is the LDAP host (can be FQDN or IP address)
ldapHost = env['UofI.ldap.ad_sys']
# this is the LDAP bind user distinguished name
ldapBindDn = env['UofI.ad_bind']
# this is the LDAP bind user password
ldapBindPw = env['UofI.ad_bindpwd']
# this is the numeric Canvas course ID
canvasCourseID = '8'
# this is the distinguished name of the source AD group
userGroupDN = 'CN=canvas-mgr,OU=groups,OU=CANVAS,OU=CITES-Services,OU=CITES,OU=Urbana,DC=ad,DC=uillinois,DC=edu'
# this is the enrollment changes summary table header
enrollmentHeader = ['NetID', 'Status', 'Enrollment_ID']
#
def bind2Ldap(ldapHost, ldapBindDn, ldapBindPw):
    try:
        ldapServer = Server(ldapHost, port=636, use_ssl=True, get_info=ALL)
        ldapConn = Connection(ldapServer, ldapBindDn, ldapBindPw, auto_bind=True, read_only=True)
        return ldapConn
    except:
        return False
#
def getADGroupDN(ldapConn, groupName):
    ldapConn.search(ldapUnitDir, '(cn={})'.format(groupName))
    return ldapConn.response[0]['dn']
#
def getADGroupMembers(ldapConn, userGroupDN):
    ldapConn.search(
        search_base=userGroupDN,
        search_filter='(objectClass=group)',
        search_scope=SUBTREE,
        attributes=['member'])
    if ldapConn.entries:
        return ldapConn.entries[0]['member'].values
    return []
#
def canvasGetAllEnrollmentsInCourse(canvasAPI, canvasAuth, canvasCourseID):
    params = {'per_page': 100}
    enrollments = []
    enrollmentsURL = f"{canvasAPI}/courses/{canvasCourseID}/enrollments"
    while enrollmentsURL:
        response = requests.get(enrollmentsURL, headers=canvasAuth, params=params)
        response.raise_for_status()
        data = response.json()
        enrollments.extend(data)
        enrollmentsURL = response.links.get('next', {}).get('url')
        params = {}  # Only needed for first request
    return enrollments
#
# this is the LDAP connection object
ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)
#
# this is a list of the members in the AD group
ADresponse = getADGroupMembers(ldapConn, userGroupDN)
# this is a list of the existing enrollments in the Canvas course
CanvasResponse = canvasGetAllEnrollmentsInCourse(canvasAPI, canvasAuth, canvasCourseID)
#
if len(ADresponse) > 0:
    adGroupMembers = []
    for user in ADresponse:
        adGroupMembers.append(user.split(',')[0].replace('CN=', ''))
else:
    print("No users found in this AD group...")
    sys.exit()
#
print()
if len(CanvasResponse) > 0:
    canvasCourseEnrollees = []
    for enrollment in CanvasResponse:
        #if enrollment['role'] == 'StudentEnrollment':
        if enrollment['user']['sis_user_id']:
            canvasCourseEnrollees.append([enrollment['user']['sis_user_id'], enrollment['id']])
            #print(r['user']['sis_user_id'])
#
# setting a few variables
proceed = ''
addEnrollments = []
dropEnrollments = []
canvasEnrollmentChanges = []
# comparing AD group members with existing Canvas course enrollments to determine new enrollments
for netID in adGroupMembers:
    #print(netID)
    if any(netID  == sublist[0] for sublist in canvasCourseEnrollees):
        canvasEnrollmentChanges.append([netID,'Enrolled - No change'])
    if not any(netID  == sublist[0] for sublist in canvasCourseEnrollees):
        canvasEnrollmentChanges.append([netID,'New'])
        addEnrollments.append(netID)
# comparing Canvas course enrollments to AD members to determine enrollment drops
for userName in canvasCourseEnrollees:
    if userName[0] not in adGroupMembers:
        canvasEnrollmentChanges.append([userName[0],'Drop Enrollment'])
        dropEnrollments.append([userName[0], userName[1]])        
canvasEnrollmentChanges.sort(key=lambda x: x[0])
table = columnar(canvasEnrollmentChanges, enrollmentHeader, no_borders=True)
print(table)
print()
#
while proceed != 'y' and proceed != 'n':
    proceed = input('Proceed with these changes? (y/n): ').strip().lower()
if proceed == 'y':
    # Add enrollments
    for change in addEnrollments:
        enrollURL = f"{canvasAPI}/courses/{canvasCourseID}/enrollments"
        # Section Enrollments
        #enrollURL = f"{canvasAPI}/sections/{sectionID}/enrollments"
        enrollParams = {"enrollment[user_id]":f"sis_user_id:{change}",
            "enrollment[type]":"StudentEnrollment",
            "enrollment[enrollment_state]":"active",
            "enrollment[notify]":"false"}
        r = requests.post(enrollURL, headers=canvasAuth, params=enrollParams)
        #pprint(r.text)
        #input('enter to continue...')
    for change in dropEnrollments:
        dropURL = f"{canvasAPI}/courses/{canvasCourseID}/enrollments/{change[1]}"
        # Section Enrollments
        #dropURL = f"{canvasAPI}/sections/{sectionID}/enrollments/{change[2]}"
        dropParams = {"task":"conclude"}
        r = requests.delete(dropURL, headers=canvasAuth, params=dropParams)
    print()
    updatedEnrollments = canvasGetAllEnrollmentsInCourse(canvasAPI, canvasAuth, canvasCourseID)
    updatedEnrollmentsTable = []
    for enrollee in updatedEnrollments:
        netid = enrollee['user']['sis_user_id']
        name = enrollee['user']['sortable_name']
        role = enrollee['role']
        enrollment_state = enrollee['enrollment_state']
        enrollment_id = enrollee['id']
        updatedEnrollmentsTable.append([netid, name, role, enrollment_state, enrollment_id])
    updatedEnrollmentsTable.sort(key=lambda x: x[1])
    print()
    print(f'Updated list of active course enrollments: ')
    table = columnar(updatedEnrollmentsTable, ['NetID', 'Name', 'Role', 'Enrollment State', 'Enrollment ID'], no_borders=True)
    print(table)
    print()
    print(f'All changes are complete. Closing connection to {canvasAPI}')
    print()
elif proceed == 'n':
    print("No changes made.")
    print()
else:
    print("Invalid input. Please enter 'y' or 'n'.")
    print()
#
#if __name__ == '__main__':
#    groupDN = getADGroupDN(ldapConn, userGroup)
#    groupUSers = getADGroupMembers(ldapconn, groupDN)
