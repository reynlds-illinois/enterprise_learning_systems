#!/usr/bin/python
#
from sqlalchemy import create_engine, text
import csv, sys, argparse, datetime
from datetime import datetime
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import logScriptStart
from canvasFunctions import connect2Box
from canvasFunctions import upload2Box
from canvasFunctions import realm
from columnar import columnar
#
logScriptStart()
realm = realm()
print('')
columnHeaders = ['space', 'status', 'owner', 'requestor', 'hold', 'course_id', 'requested']
allSpaces = []
#
dbUser = realm['sraDbUser']
dbPass = realm['sraDbPass']
dbHost = realm['sraDbHost']
dbPort = 1521
dbSid = realm['sraDbSid']
envLabel = realm['envLabel']
boxTargetFolderId = '306147770193'
boxClient = connect2Box()
statusCode = ''
nextAction = ''
allStatuses = ['a', '10', '15', '60', '315', '360', '990', '995', '999']
print('')
print(f"Connected to:  {dbHost}:{dbPort}")
print('')

# Create SQLAlchemy engine
connection_string = f"oracle+cx_oracle://{dbUser}:{dbPass}@{dbHost}:{dbPort}/?service_name={dbSid}"
engine = create_engine(connection_string)

with engine.connect() as connection:
    print('|------------------------------------------')
    print('| Available status codes (choose one):')
    print('|')
    print('|    10:  On hold for manual processing')
    print('|    15:  Ready for site creation')
    print('|    60:  Request Complete')
    print('|   315:  Canvas course ready to build')
    print('|   360:  Canvas course ready for use')
    print('|   990:  Course delete requested')
    print('|   995:  Course delete failed')
    print('|   999:  Course deleted successfully')
    print('|------------------------------------------')
    print()
    while statusCode not in allStatuses:
        statusCode = input('  Please enter a status code or (a)ll:  ').lower()
        print()
    if statusCode == 'a':
        resultStatus = 'All spaces and all statuses that are waiting:'
        spacesWaitingSql = text("""SELECT SR.SPACE_ID SPACE_ID,
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
            SR.COPY_SOURCE_SPACE_ID
        FROM CORREL.T_SPACE_REQUEST sr
            join CORREL.T_BB9_SPACE_REQUEST bsr on(SR.SPACE_ID = BSR.SPACE_REQUEST_PTR_ID)
            join CORREL.T_STATUS s on(SR.STATUS_ID = S.ID)
            join CORREL.T_CREATE_METHOD cm on(SR.CREATE_METHOD_ID = CM.CODE)
            join CORREL.T_USER uo on(SR.OWNER_ID = UO.USER_ID)
            join CORREL.T_USER ur on(SR.REQUESTER_ID = UR.USER_ID)
            left join CORREL.T_TERM TM on(SR.TERM_ID = TM.TERM_ID)
        WHERE S.CODE not in (999,60,170,350,360,370,898,899)
            OR (SR.MANUAL_PROCESSING != 0 and S.CODE != 999)
        ORDER BY SR.SPACE_ID desc""")
    else:
        resultStatus = f'All spaces that are waiting with status: {statusCode}'
        spacesWaitingSql = text(f"""SELECT SR.SPACE_ID SPACE_ID,
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
            SR.COPY_SOURCE_SPACE_ID
        FROM CORREL.T_SPACE_REQUEST sr
            join CORREL.T_BB9_SPACE_REQUEST bsr on(SR.SPACE_ID = BSR.SPACE_REQUEST_PTR_ID)
            join CORREL.T_STATUS s on(SR.STATUS_ID = S.ID)
            join CORREL.T_CREATE_METHOD cm on(SR.CREATE_METHOD_ID = CM.CODE)
            join CORREL.T_USER uo on(SR.OWNER_ID = UO.USER_ID)
            join CORREL.T_USER ur on(SR.REQUESTER_ID = UR.USER_ID)
            left join CORREL.T_TERM TM on(SR.TERM_ID = TM.TERM_ID)
        WHERE S.CODE = :statusCode
        ORDER BY SR.SPACE_ID desc""")

    results = connection.execute(spacesWaitingSql, {"statusCode": statusCode}).fetchall()
    if len(results) > 0:
        print('|=============================================')
        print(f'| Total records returned: {len(results)}')
        print('|=============================================')
        print('')
        while nextAction != 'a' and nextAction != 'f' and nextAction != 'e' and nextAction != 'q':
            nextAction = input('show (a)ll records, show (f)irst 10 records, (e)xport to CSV, (q)uit: ').strip().lower()
        print()
        if nextAction == 'a':
            listResults = []
            for row in results:
                listResults.append([row[0], row[1], row[6], row[7], row[8], row[9], row[10]])
            fullResultsTable = columnar(listResults, columnHeaders, no_borders=True)
            print(fullResultsTable)
        elif nextAction == 'e':
            listResults = []
            print('|=============================================')
            print('| Exporting to CSV...')
            for row in results:
                listResults.append([row[0], row[1], row[6], row[7], row[8], row[9], row[10]])
            now = datetime.now().timestamp()
            targetFileName = f'req_space_waiting_{now}.csv'
            targetFilePath = f'/var/lib/canvas-mgmt/reports/{targetFileName}'
            with open(targetFilePath, 'w') as exportFile:
                write = csv.writer(exportFile, delimiter='|')
                write.writerow(columnHeaders)
                write.writerows(listResults)
                print(f'| CSV export file: {targetFilePath}')
                print('|=============================================')
                print('')
            try:
                r = boxClient.folder(boxTargetFolderId).upload(targetFilePath, targetFileName)
                newFileID = r.response_object['id']
                print()
                print('|=============================================')
                print('| CSV uploaded to:  https://uofi.app.box.com/folder/306147770193')
                print('|')
                print(f'| Direct BOX file link:  https://uofi.app.box.com/file/{newFileID}')
                print('|=============================================')
                print()
            except:
                print()
                print('### Unsuccessful upload of CSV file to BOX')
                print()
            print()
        elif nextAction == 'f':
            listResults = []
            for row in results[0:9]:
                listResults.append([row[0], row[1], row[6], row[7], row[8], row[9], row[10]])
            appendedResultsTable = columnar(listResults, columnHeaders, no_borders=True)
            print(appendedResultsTable)
        else:
            print('')
            print('Exiting...')
        print('')
    else:
        print('')
        print(f"No waiting spaces in status {statusCode} on SRA {envLabel} right now...exiting...")
        print('')
