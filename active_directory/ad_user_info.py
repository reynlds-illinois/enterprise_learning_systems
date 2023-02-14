#!/usr/bin/python
#
import sys, os, time, logging, requests,urllib, ldap3, json, cx_Oracle
from ldap3 import Server, Connection, ALL
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import bind2Ldap
from canvasFunctions import logScriptStart
#
logScriptStart()
print('')
envDict = getEnv()
ldapHost = envDict['UofI.ldap.ad_sys']
ldapBindDn = envDict['UofI.ad_bind']
ldapBindPw = envDict['UofI.ad_bindpwd']
ldapSearchBase = envDict['ad-prod.searchbase_new']
#
ldapConn = bind2Ldap(ldapHost, ldapBindDn, ldapBindPw)
#
netID = input("Enter the NetID:  ")
adFilter = '(&(objectclass=user)(sAMAccountName=' + netID  + '))'
#
adQuery = ldapConn.search(search_base=ldapSearchBase, search_filter=adFilter,
          attributes = ['sAMAccountName', 'uiucEduUIN',  'uiucEduFirstName',
                       'uiucEduLastName', 'uiucEduPreviousNetID',
                       'uiucEduSuppress', 'uiucEduRegistryModifyDate',
                       'createTimeStamp', 'modifyTimeStamp', 'Enabled',
                       'uiucEduType', 'uiucEduRegistryCreateDate'],
                       size_limit=0)
#
temp = json.loads(ldapConn.response_to_json())
#
joined = temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][0] + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][1] + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][2] + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][3] + "-" + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][4] + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][5] + "-" + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][6] + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][7] + " " + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][8] + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][9] + ":" + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][10] + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][11] + ":" + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][12] + temp['entries'][0]['attributes']['uiucEduRegistryCreateDate'][13]
lastMod = temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][0] + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][1] + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][2] + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][3] + "-" + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][4] + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][5] + "-" + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][6] + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][7] + " " + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][8] + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][9] + ":" + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][10] + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][11] + ":" + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][12] + temp['entries'][0]['attributes']['uiucEduRegistryModifyDate'][13]
#
if not temp['entries'][0]['attributes']['Enabled']:
    availability = "Yes"
else:
    availability = temp['entries'][0]['attributes']['Enabled']
if not temp['entries'][0]['attributes']['Enabled']:
    previously = "n/a"
else:
    previously = temp['entries'][0]['attributes']['Enabled']
if not temp['entries'][0]['attributes']['uiucEduSuppress']:
    suppressed = "No"
else:
    suppressed = "Yes"
#
print("")
print("NetID         =", temp['entries'][0]['attributes']['sAMAccountName'])
print("UIN           =", temp['entries'][0]['attributes']['uiucEduUIN'])
print("First Name    =", temp['entries'][0]['attributes']['uiucEduFirstName'])
print("Last Name     =", temp['entries'][0]['attributes']['uiucEduLastName'])
print("Affiliation   =", temp['entries'][0]['attributes']['uiucEduType'])
print("Joined UofI   =", joined)
print("Last Modified =", lastMod)
print("Available     =", availability)
print("Suppressed    =", suppressed)
print("Former NetID  =", previously)
print("")
#
#ldapConn.close()
