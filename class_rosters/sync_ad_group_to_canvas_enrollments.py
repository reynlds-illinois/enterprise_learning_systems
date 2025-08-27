#!/usr/bin/python
#
import sys, requests
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from columnar import columnar
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import realm
#
env = getEnv()
#
canvasAPI = 'https://illinoisedu.beta.instructure.com/api/v1'
canvasToken = env['canvas.token']
canvasAuth = {"Authorization": f"Bearer {canvasToken}"}
ldapHost = env['UofI.ldap.ad_sys']
ldapBindDn = env['UofI.ad_bind']
ldapBindPw = env['UofI.ad_bindpwd']
adGroupMembers = []
canvasCourseEnrollees = []
canvasEnrollmentChanges = []
canvasCourseID = '61284'
enrollmentHeader = ['NetID', 'Status']
proceed = ''
#ldapRosterSearchBase = "OU=Class Rosters,OU=Register,OU=Urbana,DC=ad,DC=uillinois,DC=edu"
#ldapUserSearchBase = "OU=Urbana,DC=ad,DC=uillinois,DC=edu"
#
def bind2Ldap(ldapHost, ldapBindDn, ldapBindPw):
    try:
        ldapServer = Server(ldapHost, port=636, use_ssl=True, get_info=ALL)
        ldapConn = Connection(ldapServer, ldapBindDn, ldapBindPw, auto_bind=True, read_only=True)
        return ldapConn
    except:
        return False
ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)
#
#groupName = input('Enter the AD group name: ')
#ldapUsersDir = 'OU=Users,DC=test,DC=local'
#ldapUnitDir = 'OU=groups,OU=CANVAS,OU=CITES-Services,OU=CITES,OU=Urbana,DC=ad,DC=uillinois,DC=edu'
userGroupDN = 'CN=canvas-mgr,OU=groups,OU=CANVAS,OU=CITES-Services,OU=CITES,OU=Urbana,DC=ad,DC=uillinois,DC=edu'
#
ldapConn.search(ldapUnitDir, '(cn={})'.format(userGroup))
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
ADresponse = getADGroupMembers(ldapConn, userGroupDN)
CanvasResponse = canvasGetAllEnrollmentsInCourse(canvasAPI, canvasAuth, canvasCourseID)

if len(ADresponse) > 0:
    for user in response:
        adGroupMembers.append(user.split(',')[0].replace('CN=', ''))
        #print(user.split(',')[0].replace('CN=', ''))
else: print("No users found in this group...")
print()
if len(CanvasResponse) > 0:
    for enrollment in CanvasResponse:
        if enrollment['role'] == 'StudentEnrollment':
            if enrollment['user']['sis_user_id']:
                canvasCourseEnrollees.append([enrollment['user']['sis_user_id'], enrollment['id']])
                #print(r['user']['sis_user_id'])

for netID in adGroupMembers:
    if netID in canvasCourseEnrollees:
        canvasEnrollmentChanges.append([netID,'Enrolled - No change'])
    if netID not in canvasCourseEnrollees:
        canvasEnrollmentChanges.append([netID,'New Enrollment'])
for userName in canvasCourseEnrollees:
    if userName not in adGroupMembers:
        canvasEnrollmentChanges.append([userName,'Drop Enrollment', userName[1]])
table = columnar(canvasEnrollmentChanges, enrollmentHeader, no_borders=True)
print(table)
print()
#
while proceed != 'y' and proceed != 'n':
    proceed = input('Proceed with these changes? (y/n): ').strip().lower()
if proceed == 'y':
    for change in canvasEnrollmentChanges:
        if change[1] == 'New Enrollment':
            print(f"Enrolling {change[0]}...")
            # Course Enrollments
            enrollURL = f"{canvasAPI}/courses/{canvasCourseID}/enrollments"
            # Section Enrollments
            #enrollURL = f"{canvasAPI}/sections/{sectionID}/enrollments"
            enrollParams = {"enrollment[user_id]":change[0],
                "enrollment[type]":"StudentEnrollment",
                "enrollment[enrollment_state]":"active",
                "enrollment[notify]":"false"}
            r = requests.post(enrollURL, headers=canvasAuth, params=enrollParams)
        elif change[1] == 'Drop Enrollment':
            print(f"Dropping {change[0]}...")
            # Course Enrollments
            dropURL = f"{canvasAPI}/courses/{canvasCourseID}/enrollments/{change[2]}"
            # Section Enrollments
            #dropURL = f"{canvasAPI}/sections/{sectionID}/enrollments/{change[2]}"
            dropParams = {"task":"conclude"}
            r = requests.post(dropURL, headers=canvasAuth, params=dropParams)
elif proceed == 'n':
    print("No changes made.")
else:
    print("Invalid input. Please enter 'y' or 'n'.")

if __name__ == '__main__':
    groupDN = getADGroupDN(ldapConn, userGroup)
    groupUSers = getADGroupMembers(ldapconn, groupDN)




