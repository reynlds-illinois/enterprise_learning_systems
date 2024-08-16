#!/usr/bin/python
#
import time, sys, boxsdk, os, ldap3
from ldap3 import Server, Connection, ALL
from boxsdk import JWTAuth, Client
from boxsdk.exception import BoxAPIException
from datetime import datetime
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
global valid_date
yes = set(['yes','y','ye',''])
no = set(['no','n'])
#
# ENVIRONMENT AND VARIABLES
env = getEnv()
uiucDomain = env['UofI.ldap.ad_sys']
uiucLdapBindDn = env['UofI.ad_bind']
uiucRootDn = env['UofI.searchbase']
uiucGuestDn = env['uofi.box.guest.dn']
uiucLdapBindPw = env['UofI.ad_bindpwd']
uiucLdapHost = env['uofi.box.ldap.host']
uiucGroupDn = env['uofi.box.group.dn']
uiucLdapPort = int(env['uofi.box.ldap.port'])
uiucLdapSearchBase = env['uofi.box.netid.searchbase']
uiucGuestUserLdifAttr = {}
now = int(time.time())
thisYear = int(time.strftime('%Y'))
#boxAuth = JWTAuth.from_settings_file(env['uofi.box.jwtauth.file'])
boxAuth = JWTAuth.from_settings_file('/path/to/my/JWT_FILE.json')        # < update
boxClient = Client(boxAuth)
boxGuestParentFolderId = 'MY_BOX_FOLDER_ID'     # < update
boxGuestParentFolder = boxClient.folder(folder_id = boxGuestParentFolderId).get()
boxPerms = 'Viewer'
boxGuestCredentialsFilePath = '/path/to/my/reports' + str(now) + '.txt'
#
# CONNECT TO LDAP
try:
    uiucLdapConn = bind2Ldap(uiucLdapHost, uiucLdapBindDn, uiucLdapBindPw)
    print('=== SUCCESSFULLY CONNECTED TO LDAP ===')
except:
    print('=== NOT CONNECTED TO LDAP ===')
#
# CREATE GUEST ACCOUNT
if uiucLdapConn.bound == True:
    while True:
        uiucGuestUser = input('New Guest Username:  ')
        searchResult = str(ldapSearchByNetId(uiucLdapConn, uiucLdapSearchBase, uiucGuestUser))
        ### check netid availability
        if searchResult == 'True':
            print('That account already exists, please try again.')
            continue
        else:
            print('=== Account available, continuing...')
            break
    #
    uiucGuestUserDn = 'CN=' + uiucGuestUser + ',' + uiucGuestDn
    uiucGuestUserFirstName = input('First Name: ')
    uiucGuestUserLastName = input('Last Name: ')
    uiucGuestCaRequest = input('CA Request: ')
    uiucGuestRequestor = input('CA Requestor Email: ')
    while True:
        try:
            uiucGuestAccountExpire = input('Enter a date in this format YYYY-MM-DD:  ')
            datetime.strptime(uiucGuestAccountExpire, '%Y-%m-%d')
            break
        except:
            print(uiucGuestAccountExpire + ' is invalid. Please try again: '),
            continue
    ### convert to epoch for AD
    try:
        uiucGuestAccountExpireEpoch = str(get_epoch(uiucGuestAccountExpire))
        print('=== EXPIRATION DATE SET ===')' + uiucGuestAccountExpirationEpoch)
    except:
        print('>>> expiration NOT set <<<')
    ### create password
    try:
        uiucGuestUserPw = str(gen_guest_pwd())
        print('=== PASSWORD GENERATED ===')
    except:
        print('>>> password NOT generated <<<')
    boxGuestCredentialsFilename = str(uiucGuestCaRequest + '.txt')
    ### format
    try:
        uiucGuestUserLdifAttr = {}
        uiucGuestUserLdifAttr['objectClass'] = ['top', 'Person', 'organizationalPerson', 'user']
        uiucGuestUserLdifAttr['cn'] = uiucGuestUser
        uiucGuestUserLdifAttr['sAMAccountName'] = uiucGuestUser
        uiucGuestUserLdifAttr['userAccountControl'] = '514'
        uiucGuestUserLdifAttr['givenName'] = uiucGuestUserFirstName
        uiucGuestUserLdifAttr['sn'] = uiucGuestUserLastName
        uiucGuestUserLdifAttr['description'] = uiucGuestCaRequest
        uiucGuestUserLdifAttr['accountExpires'] = uiucGuestAccountExpireEpoch
        print('=== LDIF ATTRIBUTES SET ===')
    except:
        print('>>> ldif attributes NOT set <<<')
    ### add formatted user to AD
    try:
        myResult = uiucLdapConn.add(uiucGuestUserDn, attributes=uiucGuestUserLdifAttr)
        uiucLdapConn.extend.microsoft.modify_password(uiucGuestUserDn, uiucGuestUserPw)
        uiucLdapConn.modify(uiucGuestUserDn, {'primaryGroupID':(2,['513'])})
        uiucLdapConn.modify(uiucGuestUserDn, {'userAccountControl':(2,['512'])})
        uiucLdapConn.extend.microsoft.unlock_account(uiucGuestUserDn)
        print('=== AD ACCOUNT SUCCESSFULLY CREATED ===')
    except:
        print('=== AD ACCOUNT NOT CREATED ---')
else:
    print('=== CANNOT BIND TO LDAP ===')
# WRITE CREDENTIALS TO TEMP FILE
try:
    with open(boxGuestCredentialsFilePath, 'a') as boxGuestCredentialsFilePathWriteable:
        boxGuestCredentialsFilePathWriteable.write('Username:  ' + uiucGuestUser + '\n')
        boxGuestCredentialsFilePathWriteable.write('Password:  ' + uiucGuestUserPw + '\n')
        boxGuestCredentialsFilePathWriteable.write('Expires:   ' + uiucGuestAccountExpire + '\n')
    boxGuestCredentialsFilePathWriteable.close()
    print('=== CREDENTIALS FILE SUCCESSFULLY CREATED ===')
except:
    print('=== CREDENTIALS FILE NOT CREATED ===')
# CREATE GUEST SUBFOLDER IN BOX
try:
    boxGuestFolderName = uiucGuestCaRequest
    boxCreateGuestFolder = boxClient.folder(boxGuestParentFolderId).create_subfolder(boxGuestFolderName)
    boxGuestFolderId = int(boxCreateGuestFolder['id'])
    print('=== GUEST FOLDER SUCCESSFULLY CREATED IN BOX ===')
except:
    print('=== GUEST FOLDER NOT CREATED ===')
# UPLOAD TEMP FILE TO GUEST SUBFOLDER
try:
    r = boxClient.folder(boxGuestFolderId).upload(boxGuestCredentialsFilePath, boxGuestCredentialsFilename)
    print(r)
    print('=== TEMP FILE SUCCESSFULLY UPLOADED ===')
except:
    print('=== TEMP FILE NOT UPLOADED ===')
# SHARE FOLDER TO REQUESTOR
try:
    tempResult = boxClient.folder(boxGuestFolderId).create_shared_link()
    boxClient.folder(boxGuestFolderId).collaborate_with_login(login=uiucGuestRequestor, role='Viewer')
    boxSharedLink = str(tempResult['shared_link']['url'])
    print('=== TEMP FILE SUCCESSFULLY SHARED ===')
    print('=== Shared link:  ' + boxSharedLink)
except:
    print('=== TEMP FILE NOT SHARED ===')
