#!/usr/bin/python
#
import cx_Oracle, sys, argparse
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
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
#
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
#
if not args.SPACEID:
    spaceID = input('Please enter the space ID:  ')
else:
    spaceID = args.SPACEID
#
spaceQuery = f"""select h."ID" HIST_ROW,
        to_char ( h."DATE", 'MM/DD/YY HH24:MI:SS' ) "DATE",
        u.login NETID,
        h.space_id SPACEID,
        h.event_id CODE,
        de."DESC" EVENT,
        h.detail DETAIL
from CORREL.t_history h
        join CORREL.t_date_event de on(de.code = h.event_id)
        join CORREL.t_user u on(u.user_id = h.user_id)
where h.space_id = {spaceID}
        and h.event_id not in ( 483,461,503,461,485,462,581,582 )"""
#
cursor.execute(spaceQuery)
spaceHistory = cursor.fetchall()
spaceHistory.sort(reverse=True)
#
print("")
print('|====================================================================')
for line in spaceHistory:
    print(f"| {line[1]} | {line[2]} | {line[3]} | {line[5]}({line[4]})")
print('|====================================================================')
cursor.close()
print("")
