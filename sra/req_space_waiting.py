import cx_Oracle, sys, argparse
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
from columnar import columnar
#
envDict = getEnv()
env = 'x'
logScriptStart()
print('')
columnHeaders = ['space', 'status', 'owner', 'requestor', 'hold', 'course_id', 'requested']
allSpaces = []
#
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower()[0]
    if env == 'p':
        dbUser = envDict['req-prod.db.user']
        dbPass = envDict['req-prod.db.pass']
        dbHost = envDict['req-prod.db.sys']
        dbPort = 1521
        dbSid = envDict['req-prod.db.sid']
        envLabel = "PROD"
    else:
        dbUser = envDict['req-stage.db.user']
        dbPass = envDict['req-stage.db.pass']
        dbHost = envDict['req-stage.db.sys']
        dbPort = 1521
        dbSid = envDict['req-stage.db.sid']
        envLabel = "STAGE"
print('')
print(f"Connected to:  {dbHost}:{dbPort}")
print('')
#
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
#
spacesWaitingSql = """SELECT SR.SPACE_ID SPACE_ID,
    S.CODE CODE,
    S.STATUS_ADMIN_DESC STATUS,
    CM.CREATE_METHOD_DESC METHOD,
    to_char(SR.REQUEST_DATE,'YYYYMMDDHH24MISS') || SR.SPACE_ID SORT_KEY,
    to_char(SR.REQUEST_DATE,'YYYYMMDD') || SR.SPACE_ID SORT_KEY,
    UO.LOGIN OWNER,
    UR.LOGIN REQUESTER,
    SR.MANUAL_PROCESSING HOLD,
    BSR.AUX_TARGET_PRODUCT_KEY || TM.BANNER_PART_OF_TERM || '_' || BSR.SPACE_REQUEST_PTR_ID COURSE_ID,
    to_char(SR.REQUEST_DATE,'YY-MM-DD HH24:MI') REQUESTED,
    /* to_char(SR.REQUEST_DATE,'YYYY-MM-DD HH:MI AM') REQUESTED, */
    /* to_char(SR.REQUEST_DATE,'YYYY-MM-DD') REQUESTED,  */
    SR.COPY_SOURCE_SPACE_ID
FROM CORREL.T_SPACE_REQUEST sr
    join CORREL.T_BB9_SPACE_REQUEST bsr on(SR.SPACE_ID = BSR.SPACE_REQUEST_PTR_ID)
    join CORREL.T_STATUS s on(SR.STATUS_ID = S.ID)
    join CORREL.T_CREATE_METHOD cm on(SR.CREATE_METHOD_ID = CM.CODE)
    join CORREL.T_USER uo on(SR.OWNER_ID = UO.USER_ID)
    join CORREL.T_USER ur on(SR.REQUESTER_ID = UR.USER_ID)
    left join CORREL.T_TERM TM on(SR.TERM_ID = TM.TERM_ID)
WHERE S.CODE not in (999,60,170,350,360,370,898,899)
    OR (SR.MANUAL_PROCESSING != 0 and S.CODE != 999)"""
#
cursor.execute(spacesWaitingSql)
spacesInfo = cursor.fetchall()
if len(spacesInfo) > 0:
    for row in spacesInfo:
        allSpaces.append([row[0], row[1], row[6], row[7], row[8], row[9], row[10]])
    spacesTable = columnar(allSpaces, columnHeaders, no_borders=True)
    print('')
    print(spacesTable)
    print('')
else:
    print('')
    print(f"No spaces waiting on SRA {envLabel} right now.")
    print('')
cursor.close()
