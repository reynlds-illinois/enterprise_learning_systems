def dmiGetInfo():
    '''Pulls unit/department info from the DMI'''
    dmiR = requests.get('https://dmi.illinois.edu/ddd/mkexcel.aspx?role=0&roleDesc=Execute%20Officer')
    dmiConverted = pd.read_excel(dmiR.content).to_csv(index=None, header=True, encoding='utf-8', sep='|').splitlines()
    dmiTempList = []
    for row in dmiConverted:
        dmiTempList.append(row.split('|'))
    dmiTargetList = []
    for row in dmiTempList:
        c_dept = row[17].replace('-','')
        deptname = row[0].rstrip()
        collname = row[18].rstrip()
        dmiTargetList.append([deptname, row[9], row[15], c_dept, collname])
    return dmiTargetList
#
def convertDate(utcTempValue):
    '''Converts a Camvas UTC timestamp to US Central'''
    import datetime, pytz
    from datetime import datetime
    try:
        UTCvalue = datetime.strptime(utcTempValue, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
        centralValue = UTCvalue.astimezone(pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S')
        return centralValue
    except ValueError:
        pass
#
def canvasJsonDates(jsonObj):
    import pytz
    from datetime import datetime
    if isinstance(jsonObj, dict):
        for key, value in jsonObj.items():
            if isinstance(value, dict):
                canvasJsonDates(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        canvasJsonDates(item)
                    else:
                        continue
            else:
                if isinstance(value, str):
                    try:
                        UTCvalue = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
                        centralValue = UTCvalue.astimezone(pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S')
                        jsonObj.update({key:centralValue})
                    except ValueError:
                        pass
                    try:
                        datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z')
                        value = datetime.fromisoformat(value)
                        centralValue = value.astimezone(pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S')
                        jsonObj.update({key:centralValue})
                    except ValueError:
                        pass
                else:
                    continue
    elif isinstance(jsonObj, list):
        for item in jsonObj:
            #for key, value in jsonObj.items():
            if isinstance(item, dict):
                canvasJsonDates(item)
            elif isinstance(item, list):
                for item in value:
                    if isinstance(item, dict):
                        canvasJsonDates(item)
                    else:
                        continue
            else:
                if isinstance(value, str):
                    try:
                        UTCvalue = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
                        centralValue = UTCvalue.astimezone(pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S')
                        jsonObj.update({key:centralValue})
                    except ValueError:
                        pass
                    try:
                        datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z')
                        value = datetime.fromisoformat(value)
                        centralValue = value.astimezone(pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S')
                        jsonObj.update({key:centralValue})
                    except ValueError:
                        pass
                else:
                    continue
    return jsonObj
#
def chooseEnv():
    '''Choose the Canvas/SRA environment to use.'''
    import os, sys
    sys.path.append("/var/lib/canvas-mgmt/bin")
    from canvasFunctions import getEnv
    envDict = getEnv()
    envOptions = {'canvasApi':'', 'canvasWriteToken':'', 'canvasReadToken': '', 'sraDbUser':'', 'sraDbPass':'', 'sraDbHost':'', 'sraDbSid':'', 'sraDbPort':1521, 'envLabel':'', 'canvasUrl':'', 'canvasUrbanaID':'', 'canvasTerms':''}
    env = ''
    print('')
    while env != 'p' and env != 's' and env != 'c':
        env = input('Please enter the realm to use: (p)rod, (s)tage or (c)loud-DEV (SRA): ').lower().strip()
        if env == 'p':    #PRODUCTION
            envOptions['canvasApi'] = envDict['canvas.api-prod']
            envOptions['canvasReadToken'] = envDict['canvas.ro-token']
            envOptions['canvasWriteToken'] = envDict['canvas.write-token']
            envOptions['sraDbUser'] = envDict['req-prod.db.user']
            envOptions['sraDbPass'] = envDict['req-prod.db.pass']
            envOptions['sraDbHost'] = envDict['req-prod.db.sys']
            envOptions['sraDbPort'] = 1521
            envOptions['sraDbSid'] = envDict['req-prod.db.sid']
            envOptions['envLabel'] = 'PROD'
        elif env == 's':  #STAGING/BETA
            envOptions['canvasApi'] = envDict['canvas.api-beta']
            envOptions['canvasReadToken'] = envDict['canvas.ro-token']
            envOptions['canvasWriteToken'] = envDict['canvas.write-token']
            envOptions['sraDbUser'] = envDict['req-stage.db.user']
            envOptions['sraDbPass'] = envDict['req-stage.db.pass']
            envOptions['sraDbHost'] = envDict['req-stage.db.sys']
            envOptions['sraDbPort'] = 1521
            envOptions['sraDbSid'] = envDict['req-stage.db.sid']
            envOptions['envLabel'] = 'STAGE'
        else:             # SRA CLOUD-DEV
            envOptions['dbUser'] = envDict['req-cloud-dev.db.user']
            envOptions['dbPass'] = envDict['req-cloud-dev.db.pass']
            envOptions['dbHost'] = envDict['req-cloud-dev.db.sys']
            envOptions['dbPort'] = 1521
            envOptions['dbSid'] = envDict['req-cloud-dev.db.sid']
            envOptions['envLabel'] = 'SRA Cloud-Dev'
        envOptions['canvasUrl'] = envOptions['canvasApi'].strip('api/v1/')
        envOptions['canvasUrbanaID'] = '1'
        envOptions['canvasTerms'] = envDict['canvas.terms'].split(',')
        print('')
    return envOptions
#
def realm():
    '''Choose the Canvas/SRA environment to use. All settings are wrapped into a REALM'''
    import os, sys
    sys.path.append("/var/lib/canvas-mgmt/bin")
    from canvasFunctions import getEnv
    envDict = getEnv()
    realmInput = ''
    realmOptions = {}
    print('')
    #while realmInput != 'p' and realmInput != 's' and realmInput != 'c' and realmInput != 't':
    while realmInput != 'p' and realmInput != 'b' and realmInput != 't':
        realmInput = input('Please enter the realm to use: (p)rod, (b)eta/dev or (t)est/dev: ').lower().strip()
        if realmInput == 'p':    #PRODUCTION
            realmOptions['canvasApi'] = envDict['canvas.api-prod']
            realmOptions['canvasToken'] = envDict['canvas.token']
            realmOptions['sraDbUser'] = envDict['req-prod.db.user']
            realmOptions['sraDbPass'] = envDict['req-prod.db.pass']
            realmOptions['sraDbHost'] = envDict['req-prod.db.sys']
            realmOptions['sraDbPort'] = 1521
            realmOptions['sraDbSid'] = envDict['req-prod.db.sid']
            realmOptions['envLabel'] = 'CANVAS-PROD/SRA-PROD'
            realmOptions['canvasUrl'] = envDict['canvas.api-prod'].strip('api/v1/')
            realmOptions['crHost'] = envDict['class.rosters.host']
            realmOptions['crXapikey'] = envDict['class.rosters.xapi']
        elif realmInput == 'b':  #DEV/BETA
            realmOptions['canvasApi'] = envDict['canvas.api-beta']
            realmOptions['canvasToken'] = envDict['canvas.token']
            realmOptions['sraDbUser'] = envDict['req-stage.db.user']
            realmOptions['sraDbPass'] = envDict['req-stage.db.pass']
            realmOptions['sraDbHost'] = envDict['req-stage.db.sys']
            realmOptions['sraDbPort'] = 1521
            realmOptions['sraDbSid'] = envDict['req-stage.db.sid']
            realmOptions['envLabel'] = 'CANVAS-BETA/SRA-DEV'
            realmOptions['canvasUrl'] = envDict['canvas.api-beta'].strip('api/v1/')
            realmOptions['crHost'] = envDict['class.rosters.host']
            realmOptions['crXapikey'] = envDict['class.rosters.xapi']
        else:                    #TEST/BETA
            realmOptions['canvasApi'] = envDict['canvas.api-test']
            realmOptions['canvasToken'] = envDict['canvas.token']
            realmOptions['sraDbUser'] = envDict['req-stage.db.user']
            realmOptions['sraDbPass'] = envDict['req-stage.db.pass']
            realmOptions['sraDbHost'] = envDict['req-stage.db.sys']
            realmOptions['sraDbPort'] = 1521
            realmOptions['sraDbSid'] = envDict['req-stage.db.sid']
            realmOptions['envLabel'] = 'CANVAS-TEST/SRA-DEV'
            realmOptions['canvasUrl'] = envDict['canvas.api-test'].strip('api/v1/')
            realmOptions['crHost'] = envDict['class.rosters.host']
            realmOptions['crXapikey'] = envDict['class.rosters.xapi']
        realmOptions['canvasUrbanaID'] = '1'
        realmOptions['canvasTerms'] = envDict['canvas.terms'].split(',')
        realmOptions['canvasAccountId'] = '1'
        print('')
    return realmOptions
#
#---------------------------------------------------------
# CRN Lookup using Class Rosters API
#---------------------------------------------------------
def crnLookup(crHost, crXapikey, termCode, crn):
    import urllib, json, requests
    apiEndpoint = f"v1.0/section-lookup/{termCode}/{crn}"
    url = urllib.parse.urljoin(crHost, apiEndpoint)
    headers = {"X-API-KEY": crXapikey}
    response = requests.get(url, headers=headers).json()
    return response
#
#---------------------------------------------------------
# Log the initiation of a script fun and who did it
#---------------------------------------------------------
def logScriptStart():
    '''Record who initiates a Python script and when'''
    import os, sys, time
    today = str(time.strftime('%Y-%m-%d'))
    now = str(time.strftime('%Y-%m-%d %H:%M:%S'))
    currentUser = os.getlogin()
    scriptName = os.path.basename(sys.argv[0])
    logFile = f"/var/lib/canvas-mgmt/logs/{today}.log"
    if not os.path.exists(logFile):
        os.mknod(logFile)
    with open(logFile, 'a') as targetLog:
        targetLog.write(f"{now} | {currentUser} | {scriptName}" + "\n")
#
#---------------------------------------------------------
# look up a Canvas User ID based on NetID input
#---------------------------------------------------------
def canvasGetUserInfo(netID):
    import csv, os, sys
    with open('/var/lib/canvas-mgmt/config/canvas_users.csv', 'r') as csvFile:
        reader = csv.reader(csvFile)
        for row in reader:
            if row[1] == netID:
                return row
            else:
                continue
        return "False"
#
#---------------------------------------------------------
# look up UNIT sub-accounts
#---------------------------------------------------------
def canvasGetAccountUnits():
    import csv, os, sys
    uiucUnits = []
    with open('/var/lib/canvas-mgmt/config/canvas_accounts.csv', 'r') as csvFile:
        reader = csv.reader(csvFile)
        for row in reader:
            if 'UNIT_' in row[1]:
                uiucUnits.append(row)
        if len(uiucUnits) == 0:
            return "False"
        else:
            return uiucUnits
#
#--------------------------------------------------------
# look up Canvas Account ID from UIUC Unit
#--------------------------------------------------------
def canvasGetAccountID(uiucAccount):
    import csv, os, sys
    with open('/var/lib/canvas-mgmt/config/canvas_accounts.csv', 'r') as csvFile:
        reader = csv.reader(csvFile)
        for row in reader:
            if row[1] == uiucAccount:
                canvasAccountID = row[0]
                break
            else:
                continue
        if len(canvasAccountID) > 0:
            return canvasAccountID
        else:
            return "False"
#
#---------------------------------------------------------
# perform lookups on batches of CRNs
#---------------------------------------------------------
def batchLookupReg(crHost, crXapikey, termcode: str, crns: list) -> dict:
    '''perform lookups on batches of CRNs'''
    import urllib,requests
    api_endpoint = "v1.0/registrations/crns"
    url = urllib.parse.urljoin(crHost, api_endpoint)
    headers = {"X-API-KEY": crXapikey}
    data = {"termcode": termcode, "crns": crns}
    response = requests.post(url, headers=headers, json=data)
    return response.json()
#
#---------------------------------------------------------
# connect to a SQL database
#---------------------------------------------------------
def connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid):
    '''create a connection to a SQL database'''
    import cx_Oracle, sys
    oraConn = cx_Oracle.connect('%s/%s@%s:%s/%s' % (dbUser, dbPass, dbHost, dbPort, dbSid))
    cursor = oraConn.cursor()
    return cursor
#
#---------------------------------------------------------
# Get today's date in this format:  '2022-09-01'
#---------------------------------------------------------
def today():
   """Return the current date as a string"""
   import time
   return str(time.strftime('%Y-%m-%d'))
#
#---------------------------------------------------------
# Get date/time in this format: '2022-09-01 09:45:19'
#---------------------------------------------------------
def now():
    """Return the current date/time as a string"""
    import time
    return str(time.strftime('%Y-%m-%d %H:%M:%S'))
#
#---------------------------------------------------------
# Converts a UIUC Section ID to a Canvas Section ID
#---------------------------------------------------------
def findCanvasSection(netId):
    """Return Canvas Section ID when UIUC SIS Section ID is provided"""
    import csv
    #netId = input("Enter NetID:  ")
    csv_file = csv.reader(open("/var/lib/canvas-mgmt/config/canvas_sections.csv", "r", encoding="utf-8"), delimiter=",")
    for row in csv_file:
        if netId == row[1]:
            #print (row)
            return str(row[0])
#
#---------------------------------------------------------
# Returns a list of sections in a Canvas course
#---------------------------------------------------------
def findCanvasSections(canvasCourseId):
    """Return rows from Canvas sections"""
    import csv
    returnList = []
    with open("/var/lib/canvas-mgmt/config/canvas_sections.csv") as csv_file:
        csvF = csv.reader(csv_file, delimiter=",")
        for row in csvF:
            #print(row[3])
            if canvasCourseId == row[3]:
                returnList.append(row)
                #print(row)
                continue
    #print("Complete")
    return returnList
#
#---------------------------------------------------------
# Converts a UIUC NetID to a Canvas ID (string)
#---------------------------------------------------------
def findCanvasUser(netId):
    """Return Canvas user ID when UIUC NetID is provided"""
    import csv
    #netId = input("Enter NetID:  ")
    csv_file = csv.reader(open("/var/lib/canvas-mgmt/config/canvas_users.csv", "r", encoding="utf-8"), delimiter=",")
    for row in csv_file:
        if netId == row[1]:
            #print (row)
            return str(row[0])
#
#---------------------------------------------------------
# Converts a UIUC course ID to a Canvas ID (string)
#---------------------------------------------------------
def findCanvasCourse(courseId):
    """Return Canvas course ID when UIUC course ID is provided"""
    import csv
    #courseId = input("Enter Course ID:  ")
    csv_file = csv.reader(open("/var/lib/canvas-mgmt/config/canvas_courses.csv", "r", encoding="utf-8"), delimiter=",")
    for row in csv_file:
        if courseId == row[1]:
            #print (row[0])
            return str(row[0])
#
#---------------------------------------------------------
# Event Log Handling
#---------------------------------------------------------
def eventLog(eventDetail, logLocation):
    '''save events into a log'''
    import time
    logFile = open(logLocation, 'a+')
    logFile.write('%s %s \n' % (time.asctime(), eventDetail))
    logFile.close()
#
#---------------------------------------------------------
# connect to a Blackboard instance using REST API
#---------------------------------------------------------
def connect2Bb(key, secret, url):
    '''create a REST connection to a Bb instance'''
    import bbrest
    from bbrest import BbRest
    try:
        bb = BbRest(key, secret, url)
        return bb
    except:
        return False
#
#---------------------------------------------------------
# create an initial connection to Box using the REST API
# requires:  from boxsdk import JWTAuth, Client
#---------------------------------------------------------
def connect2Box(boxJwtAuthFile='/services/ic-tools/config/83165_6no30ljy_config.json'):
    '''create a connection to Box using JWTAuth file'''
    from boxsdk import JWTAuth, Client
    try:
        boxAuth = JWTAuth.from_settings_file(boxJwtAuthFile)
        boxClient = Client(boxAuth)
        return boxClient
    except:
        return False
#
#---------------------------------------------------------
# Creates a subfolder in U of I Box based on the provided
# parent folder ID. Returns folder ID of new folder.
# Requires:   boxsdk, boxsdk[jwt]
#             configured Box Client, new folder name, parent folder ID
#
# 2018-11-16, reynlds@illinois.edu
#             initial config and test
#
#---------------------------------------------------------
def createBoxFolder(boxClient, boxFolderName, boxParentFolderId):
    '''create folder in Box using folder IDs'''
    try:
        createBoxFolder = boxClient.folder(boxParentFolderId).create_subfolder(boxFolderName)
        boxFolderId = int(createBoxFolder['id'])
        return boxFolderId
    except:
        return False
#
#---------------------------------------------------------
# upload a file to a folder on Box
#---------------------------------------------------------
def upload2Box(boxClient, boxTargetFolderId, sourceFilePath, sourceFilename):
    '''upload a file to a folder in Box'''
    try:
        boxClient.folder(boxTargetFolderId).upload(sourceFilePath, sourceFilename)
        return True
    except:
        return False
#
#---------------------------------------------------------
# share a folder with a user on Box
#---------------------------------------------------------
def shareBoxFolder(boxClient, boxFolderId, boxCollaboratorEmail, boxCollaboratorRole):
    '''share a folder with a user in Box'''
    try:
        tempResult = boxClient.folder(boxFolderId).create_shared_link()
        boxClient.folder(boxFolderId).collaborate_with_login(login=boxCollaboratorEmail, role=boxCollaboratorRole)
        boxSharedLink = str(tempResult['shared_link']['url'])
        return boxSharedLink
    except:
        return False
#
#---------------------------------------------------------
# get a date formated as:  YYYY-MM-DD
#---------------------------------------------------------
def getDate():
    '''format an input date and pass it back in this format YYYY-MM-DD'''
    from datetime import datetime
    while True:
        try:
            daTe = input('Enter a date in this format YYYY-MM-DD:  ')
            datetime.strptime(daTe, '%Y-%m-%d')
            break
        except:
            print(daTe + ' is invalid. Please try again: '),
            continue
    return daTe
#
#---------------------------------------------------------
# get a 24-hour time formated as:  HH:MM:SS
#---------------------------------------------------------
def getTime():
    '''format an input time and pass it back in this format HH:MM:SS'''
    import time
    while True:
        try:
            tiMe = input('Enter a 24-hour time in this format HH:MM:SS:  ')
            time.strptime(tiMe, '%H:%M:%S')
            break
        except:
            print(tiMe + ' is invalid. Please try again: '),
            continue
    return tiMe
#
#---------------------------------------------------------
# convert date (YYYY-MM-DD) to epoch specifically for use
# to modify Microsoft Active Directory objects
#---------------------------------------------------------
def date2Epoch(daTe):
    '''convert a date to epoch specifically for use by Active Directory'''
    import time
    pattern = '%Y-%m-%d %H:%M:%S'
    dateTime = str(daTe) + ' 23:59:59'
    tempDate = int(time.mktime(time.strptime(dateTime,pattern)))
    epochDate = (tempDate + 11644473600) * 10000000
    return int(epochDate)
#
#---------------------------------------------------------
# create a simple password
#---------------------------------------------------------
def createPw(newPwLength = 8):
    '''generate a simple random password - 8 chars by default'''
    import random
    from random import randint
    alphaChars = 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    specialChars = list(".,-_")
    newPw = ''
    for i in range (newPwLength):
        tempIndex = random.randrange(len(alphaChars))
        newPw = newPw + alphaChars[tempIndex]
    for i in range(random.randrange(1,3)):
        tempIndex = random.randrange(len(newPw)//2)
        newPw = newPw[0:tempIndex] + str(random.randrange(10)) + newPw[tempIndex+1:]
    randomChar = randint(2,newPwLength)
    newPwList = list(newPw)
    newPwList[randomChar] = specialChars[randomChar]
    newPw = ''.join(newPwList)
    return newPw
#
def randomPw(newPwLength = 8):
    '''updated version of createPw function'''
    newPw = ''
    from string import digits, ascii_lowercase, ascii_uppercase
    from random import choice as rc
    newPwChars = f"{ascii_uppercase}{ascii_lowercase}{digits}"
    newPw = str(''.join(rc(newPwChars) for x in range(newPwLength,20)))
    return newPw
#
#---------------------------------------------------------
# ask a simple yes or no and return true or false
#---------------------------------------------------------
def yesOrNo(question):
    '''request simple yes or no answer and pass it back'''
    while "the answer is invalid":
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[:1] == 'y':
            return True
        if reply[:1] == 'n':
            return False
#
#---------------------------------------------------------
#
# Facilitates connection to an LDAP directory or Microsoft
# Active Directory.
# Requires:   ldap3, from ldap3: Server, Connection, ALL
#             all variables a defined below
#
# 2018-11-16, reynlds@illinois.edu
#             initial config and test
#
#---------------------------------------------------------
def bind2Ldap(ldapHost, ldapBindDn, ldapBindPw):
    '''bind to a directory service like Active Directory or LDAP'''
    import ldap3
    from ldap3 import Server, Connection, ALL
    try:
        ldapServer = Server(ldapHost, port=636, use_ssl=True, get_info=ALL)
        ldapConn = Connection(ldapServer, ldapBindDn, ldapBindPw, auto_bind=True, read_only=True)
        return ldapConn
    except:
        return False
#
#---------------------------------------------------------
# check AD/ldap to see if a username already exists
# Requires a valid ldap Connection
#---------------------------------------------------------
def ldapSearchByNetId(ldapConn, ldapSearchBase, netId):
    '''search for an existing user in a directory service like AD or LDAP'''
    adFilter = '(&(objectclass=user)(sAMAccountName=' + netId  + '))'
    if ldapConn.bind():
        netIdSearch = ldapConn.search(search_base=ldapSearchBase,
                            search_filter=adFilter,
                            search_scope='SUBTREE',
                            attributes = ['sAMAccountName',
                           'displayName',
                           'userPrincipalName',
                           'givenName',
                           'sn',
                           'mail',
                           'distinguishedName'],
                            size_limit=0)
        return netIdSearch
    else:
        print('>>> Not bound to AD or LDAP <<<')
