#!/usr/bin/python
#
import sys,logging,requests,urllib, ldap3, json, cx_Oracle
from ldap3 import Server, Connection, ALL
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import batchLookupReg
from canvasFunctions import bind2Ldap
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
#
envDict = getEnv()
logScriptStart()
crHost = envDict['class.rosters.host']
crXapikey = envDict['class.rosters.xapi']
ldapHost = envDict['UofI.ldap.ad_sys']
ldapBindDn = envDict['UofI.ad_bind']
ldapBindPw = envDict['UofI.ad_bindpwd']
ldapSearchBase = envDict['ad-prod.searchbase_new']
dbUser = envDict['req-prod.db.user']
dbPass = envDict['req-prod.db.pass']
dbHost = envDict['req-prod.db.sys']
dbPort = 1521
dbSid = envDict['req-prod.db.sid']
crns = []
#
ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
print('')
spaceID = input('Enter space ID: ')
#
crnQuery = f"""SELECT SRR.ROSTER_DATA_SOURCE_KEY CRN,
       SRR.ROSTER_DATA_SOURCE_KEY CRN,
       ADR.RUBRIC,
       ADR.COURSE_NUMBER,
       ADR.SECTION,
       ADR.TERM_CODE TERM
FROM CORREL.T_SPACE_ROSTER SRR
  LEFT JOIN CORREL.T_AD_ROSTER ADR on(SRR.ROSTER_DATA_SOURCE_KEY = ADR.CRN and SRR.TERM_CODE = ADR.TERM_CODE)
WHERE SRR.SPACE_ID = {spaceID}"""
#
cursor.execute(crnQuery)
crnInfo = cursor.fetchall()
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
            adFilter = '(&(objectclass=user)(uiucEduUIN=' + uin  + '))'
            bitBkt = ldapConn.search(search_base=ldapSearchBase, search_filter=adFilter,
                attributes = ['sAMAccountName', 'displayName', 'uiucEduUIN'], size_limit=0)
            temp = json.loads(ldapConn.response_to_json())
            netId = temp['entries'][0]['attributes']['sAMAccountName']
            displayName = temp['entries'][0]['attributes']['displayName']
            print('        ', netId, '-', displayName)
print('')
