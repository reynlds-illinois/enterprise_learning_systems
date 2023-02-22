import cx_Oracle, sys, argparse
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
#
envDict = getEnv()
env = 'x'
newStatus = 0
newStatusID = 0
logScriptStart()
choice = ''
print('')
#
parser = argparse.ArgumentParser(add_help=True)
parser.add_argument('-s', dest='SPACEID', action='store', help='The globally-unique 6-digit space ID', type=str)
args = parser.parse_args()
#
while env != 'p' and env != 's':
    env = input('Please enter the realm to use: (p)rod or (s)tage: ').lower()[0]
    if env == 'p':
        dbUser = envDict['req-prod.db.suser']
        dbPass = envDict['req-prod.db.spass']
        dbHost = envDict['req-prod.db.sys']
        dbPort = 1521
        dbSid = envDict['req-prod.db.sid']
        envLabel = "PROD"
    else:
        dbUser = envDict['req-stage.db.suser']
        dbPass = envDict['req-stage.db.spass']
        dbHost = envDict['req-stage.db.sys']
        dbPort = 1521
        dbSid = envDict['req-stage.db.sid']
        envLabel = "STAGE"
print('')
print(f"Connected to: {dbHost}:{dbPort}")
print('')
#
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
#
if not args.SPACEID:
    spaceID = int(input('Please enter the space ID: '))
else:
    spaceID = int(args.SPACEID)
#
spaceInfoQuery = f"""SELECT SR.SPACE_ID SPACE_ID,
  /* non-xml elements */
  SR.TYPE_ID TYPE_ID,
  SR.CREATE_METHOD_ID CREATE_METHOD_ID,
  S.CODE STATUS,
  S.STATUS_ADMIN_DESC STATUS_DEC,
  SR.MANUAL_PROCESSING HOLD,
  CM.CREATE_METHOD_DESC CREATE_METHOD,
  to_char ( SR.REQUEST_DATE, ( 'YYYY-MM-DD HH:MI AM' ) ) REQUESTED,
  TM.BANNER_TERM BANNER,
  /* content */
  SR.COPY_SOURCE_SPACE_ID COPY_SOURCE,
  TY.CODE T_CODE,
  TY.TYPE_DESC TYPE_DESC,
  BSR.FOREIGN_COPY_SOURCE_KEY VISTA_CONTENT,
  /* language */
  BSR.LANGUAGE_ENFORCED_IND ENFORCED,
  BSR.LANGUAGE LANGUAGE,
  /* names and descriptions */
  SR.TARGET_PRODUCT_KEY || TM.BANNER_PART_OF_TERM || '_' || SR.SPACE_ID BATCH_UID,
  BSR.AUX_TARGET_PRODUCT_KEY || TM.BANNER_PART_OF_TERM || '_' || BSR.SPACE_REQUEST_PTR_ID COURSE_ID,
  TM.NAME T_TERM,
  BSR.TITLE_PREFIX T_PREFIX,
  BSR.TITLE_FREE T_FREE,
  BSR.TITLE_SECTION T_SECTION,
  BSR.DESCRIPTION COURSE_DESC,
  /* access */
  BSR.GUEST_ACCESS_IND ALLOW_GUESTS,
  BSR.CONTINUOUS CONTINUOUS,
  BSR.REQUIRE_ACCESS_CODE_IND ACCESS_CODE,
  /* orginazation */
  BSR.DISPLAY_IN_CATALOG_IND CATALOG,
  BSR.INSTITUTION INSTITUTION,
  BSR.PRIMARY_DEPARTMENT_KEY PDK,
  /* enrollment */
  BSR.ENROLL_OPT ENROLL_OPT,
  BSR.SELF_ENROLL_DURATION DAYS_OF_USE,
  to_char ( BSR.SELF_ENROLL_END_DATE, ( 'YYYY-MM-DD' ) ) ENROLL_END,
  to_char ( BSR.SELF_ENROLL_START_DATE, ( 'YYYY-MM-DD' ) ) ENROLL_START,
  BSR.SELF_ENROLL_DURATION DURATION,
  BSR.PACE PACE,
  /* owners */
  UO.LOGIN OWNER_NETID,
  UR.LOGIN REQUESTER_NETID,
  UO.USER_DATA_SOURCE_KEY OWNER_UIN,
  UR.USER_DATA_SOURCE_KEY REQUESTER_UIN,
  /* comments */
  SR.USER_COMMENTS USER_COMMENT,
  SR.STAFF_COMMENTS STAFF_COMMENT
    , to_char ( nvl ( sch_bb."DATE", tsch_bb."DATE" ) , ( 'YYYY-MM-DD' ) ) B_BEGIN
    , to_char ( nvl ( sch_be."DATE", tsch_be."DATE" ) , ( 'YYYY-MM-DD' ) ) B_END
    , to_char ( nvl ( sch_rb."DATE", tsch_rb."DATE" ) , ( 'YYYY-MM-DD' ) ) R_BEGIN
    , to_char ( nvl ( sch_re."DATE", tsch_re."DATE" ) , ( 'YYYY-MM-DD' ) ) R_END
    , to_char ( nvl ( sch_cb."DATE", tsch_cb."DATE" ) , ( 'YYYY-MM-DD' ) ) BEGIN
    , to_char ( nvl ( sch_ce."DATE", tsch_ce."DATE" ) , ( 'YYYY-MM-DD' ) ) END
FROM CORREL.T_SPACE_REQUEST SR
  JOIN CORREL.T_BB9_SPACE_REQUEST BSR on(BSR.SPACE_REQUEST_PTR_ID = SR.SPACE_ID)
  JOIN CORREL.T_USER UO on(SR.OWNER_ID = UO.USER_ID)
  JOIN CORREL.T_USER UR on(SR.REQUESTER_ID = UR.USER_ID)
  JOIN CORREL.T_TYPE TY on(SR.TYPE_ID = TY.ID)
  JOIN CORREL.T_STATUS S on(S.ID = SR.STATUS_ID)
  JOIN CORREL.T_CREATE_METHOD CM on(SR.CREATE_METHOD_ID = CM.CODE)
  LEFT JOIN CORREL.T_TERM TM on(SR.TERM_ID = TM.TERM_ID)
  LEFT JOIN CORREL.t_schedule sch_bb on ( sch_bb.space_id = sr.space_id and sch_bb.event_id = 441 )
  LEFT JOIN CORREL.t_term_schedule tsch_bb on ( tsch_bb.term_id = sr.term_id and  tsch_bb.event_id = 441 )
  LEFT JOIN CORREL.t_schedule sch_be on ( sch_be.space_id = sr.space_id and sch_be.event_id = 442 )
  LEFT JOIN CORREL.t_term_schedule tsch_be on ( tsch_be.term_id = sr.term_id and  tsch_be.event_id = 442 )
  LEFT JOIN CORREL.t_schedule sch_rb on ( sch_rb.space_id = sr.space_id and sch_rb.event_id = 445 )
  LEFT JOIN CORREL.t_term_schedule tsch_rb on ( tsch_rb.term_id = sr.term_id and  tsch_rb.event_id = 445 )
  LEFT JOIN CORREL.t_schedule sch_re on ( sch_re.space_id = sr.space_id and sch_re.event_id = 446 )
  LEFT JOIN CORREL.t_term_schedule tsch_re on ( tsch_re.term_id = sr.term_id and  tsch_re.event_id = 446 )
  LEFT JOIN CORREL.t_schedule sch_cb on ( sch_cb.space_id = sr.space_id and sch_cb.event_id = 443 )
  LEFT JOIN CORREL.t_term_schedule tsch_cb on ( tsch_cb.term_id = sr.term_id and  tsch_cb.event_id = 443 )
  LEFT JOIN CORREL.t_schedule sch_ce on ( sch_ce.space_id = sr.space_id and sch_ce.event_id = 444 )
  LEFT JOIN CORREL.t_term_schedule tsch_ce on ( tsch_ce.term_id = sr.term_id and  tsch_ce.event_id = 444 )
WHERE SR.PRODUCT_ID = 'BB9'
  AND SR.SPACE_ID in ({spaceID})"""
#
cursor.execute(spaceInfoQuery)
spaceInfo = cursor.fetchall()

print('')
print('|=============================== INFO ===============================')
print('| SPACE_ID      =', spaceInfo[0][0])
print('| STATUS        =', spaceInfo[0][3], '-', spaceInfo[0][4])
print('| COURSE_ID     =', spaceInfo[0][15])
print('|====================================================================')
oldStatus = spaceInfo[0][3]
#cursor.close()
print('')
print('| Available Statuses:  15   Build Space')
print('|                      360  Space is Ready')
print('|                      990  Space is set for Deletion')
print('|                      999  Space is Deleted')
print('')
while newStatus != 15 and newStatus != 360 and newStatus != 990 and newStatus != 999:
    newStatus = int(input("Please enter the new status for space {spaceID}: "))
if newStatus == 15:         # Status 15 is Status ID of 3
    newStatusID = 3
elif newStatus == 360:      # Status 360 is Status ID of 230
    newStatusID = 230
elif newStatus == 990:      # Status 990 is Status ID of 73
    newStatusID = 73
else:                      # Status 999 is Status ID of 27
    newStatusID = 27
print('')
while choice != 'y' and choice != 'n':
    choice = input(f">>> Change status of space {spaceID} from {oldStatus} to {newStatus} (y/n)? ").lower()[0]
print('')
if choice == 'n':
    print("Exiting without changes...")
    cursor.close()
    print('')
else:
    statusChangeSql = f"""UPDATE CORREL.t_space_request sr
                      SET sr.status_id = {newStatusID}
                      WHERE sr.product_id = 'BB9'
                          AND sr.space_id = {spaceID}"""
    cursor.execute(statusChangeSql)
    cursor.execute("COMMIT")
    print("Change successful:")
    print('')
    cursor.execute(spaceInfoQuery)
    spaceInfo = cursor.fetchall()
    print('|========================== UPDATED INFO ============================')
    print('| SPACE_ID      =', spaceInfo[0][0])
    print('| STATUS        =', spaceInfo[0][3], '-', spaceInfo[0][4])
    print('| COURSE_ID     =', spaceInfo[0][15])
    print('|====================================================================')
    cursor.close()
    print('')
