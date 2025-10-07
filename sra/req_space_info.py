from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys, argparse
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import logScriptStart

# Initialize realm and environment
realm = realm()
env = ''
logScriptStart()
print('')

# Database connection details
dbUser = realm['sraDbUser']
dbPass = realm['sraDbPass']
dbHost = realm['sraDbHost']
dbPort = 1521
dbSid = realm['sraDbSid']
envLabel = realm['envLabel']

# Create SQLAlchemy engine
db_url = f"oracle+oracledb://{dbUser}:{dbPass}@{dbHost}:{dbPort}/{dbSid}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

print('')
print(f"Connected to:  {dbHost}:{dbPort}")
print('')

while True:
    spaceID = int(input('Please enter the space ID:  '))

    # Query for space information
    spaceQuery = f"""SELECT SR.SPACE_ID SPACE_ID,
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
      TBN.SHORT_NAME DEPT_CODE, TBN.NAME AS DEPT_NAME, (SELECT TBN2.SHORT_NAME FROM CORREL.T_BB9_NODE TBN2 WHERE TBN2.NODE_ID=TBN.PARENT_NODE_ID) AS PARENT_UNIT,
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
      SR.REQUESTER_OPT_OUT,
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
      JOIN CORREL.T_BB9_NODE TBN ON TBN.CODE = BSR.PRIMARY_DEPARTMENT_KEY
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

    spaceInfo = session.execute(text(spaceQuery)).fetchall()

    # Query for CRN information
    crnQuery = f"""SELECT SRR.ROSTER_DATA_SOURCE_KEY CRN,
           SRR.ROSTER_DATA_SOURCE_KEY CRN,
           ADR.RUBRIC,
           ADR.COURSE_NUMBER,
           ADR.SECTION,
           ADR.TERM_CODE TERM
    FROM CORREL.T_SPACE_ROSTER SRR
      LEFT JOIN CORREL.T_AD_ROSTER ADR on(SRR.ROSTER_DATA_SOURCE_KEY = ADR.CRN and SRR.TERM_CODE = ADR.TERM_CODE)
    WHERE SRR.SPACE_ID = {spaceID}"""

    crnInfo = session.execute(text(crnQuery)).fetchall()

    # Query for space history
    historyQuery = f"""select h."ID" HIST_ROW,
            to_char ( h."DATE", 'YYYY/MM/DD HH24:MI:SS' ) "DATE",
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

    spaceHistory = session.execute(text(historyQuery)).fetchall()
    spaceHistory = sorted(spaceHistory, reverse=True)

    print('')
    print('|=============================== INFO ===============================')
    print('| SPACE_ID      =', spaceInfo[0][0])
    print('| REQUESTED     =', spaceInfo[0][7])
    print('| COURSE_ID     =', spaceInfo[0][15])
    print('| COURSE_NAME   =', spaceInfo[0][18], '-', spaceInfo[0][19], '-', spaceInfo[0][20])
    print('| TYPE_DESC     =', spaceInfo[0][11])
    print('| REQUESTOR     =', spaceInfo[0][38])
    print('|     OPT_OUT   =', spaceInfo[0][39])
    print('| OWNER         =', spaceInfo[0][37])
    print('| UNIT          =', spaceInfo[0][30])
    print('| DEPARTMENT    =', spaceInfo[0][28],'-', spaceInfo[0][29])
    print('| STATUS        =', spaceInfo[0][3], '-', spaceInfo[0][4])
    print('| HOLD          =', spaceInfo[0][5])
    print('| STAFF_COMMENT =', spaceInfo[0][42])
    print('| USER_COMMENT  =', spaceInfo[0][41])
    print('| CREATE_METHOD =', spaceInfo[0][6])
    print('| TERM          =', spaceInfo[0][8], '-', spaceInfo[0][17])
    print('| ACCESSIBLE    =', spaceInfo[0][47], 'to', spaceInfo[0][48])
    print('| BANNER_DATES  =', spaceInfo[0][43], 'to', spaceInfo[0][44])
    print('| ROSTER_LOAD   =', spaceInfo[0][45], 'to', spaceInfo[0][46])
    if len(crnInfo) > 0:
        print('| CRN INFO      =', crnInfo[0])
        for item in range(1, len(crnInfo)):
            print(f'|                 {crnInfo[item]}')
        print('|============================ HISTORY ===============================')
    else:
        print('| CRN INFO      =')
        print('|============================ HISTORY ===============================')
    for line in spaceHistory:
        print(f"| {line[1]} | {line[2]} | {line[3]} | {line[5]}({line[4]})")
    print('|====================================================================')
    print()
    answer = input("Continue with another space (y/n)? ").strip().lower()
    if answer != 'y':
        break

print("Closing connection and exiting...")
session.close()
print('')
