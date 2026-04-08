#
#!/usr/bin/python
#
import sys, argparse, requests, json, csv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import logScriptStart
from columnar import columnar
#
realm = realm()
env = ''
#logScriptStart()
dbUser = realm['sraDbUser']
dbPass = realm['sraDbPass']
dbHost = realm['sraDbHost']
dbPort = 1521
dbSid = realm['sraDbSid']
envLabel = realm['envLabel']
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
canvasEnvLabel = realm['envLabel']
canvasAccountId = "1"
authHeader = {"Authorization": f"Bearer {canvasToken}"}
#
sraCourseIDs = []
undeletedIDs = []
columnHeaders = ['canvas_id', 'import_id', 'sis_course_id', 'state', 'name']
#
try:
    db_url = f"oracle+oracledb://{dbUser}:{dbPass}@{dbHost}:{dbPort}/{dbSid}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    print(f"Connected to:  {dbHost}:{dbPort}")
    print(f"               {canvasApi}")
    print('')
except Exception as e:
    print(f"> Error: {e}")
    print()
#
sraQuery = """SELECT tsr.TARGET_PRODUCT_KEY || '_' || tsr.SPACE_ID AS SIS_COURSE_ID
              FROM correl.T_SPACE_REQUEST tsr
                JOIN correl.T_STATUS ts ON ts.ID = tsr.STATUS_ID
              WHERE ts.STATUS_ADMIN_DESC = 'Request canceled'"""
#
sraQueryResult = session.execute(text(sraQuery)).fetchall()
print()
print('SRA query complete...')
print()
if len(sraQueryResult) > 0:
    for item in sraQueryResult:
        sraCourseIDs.append(item[0])
#
print(f'  = {len(sraCourseIDs)} records have been identified...')
print()
print('>>> Checking Canvas courses...')
print()
#
for courseID in sraCourseIDs:
    print(f'  = {courseID}')
    url = f"{canvasApi}accounts/1/courses?search_term={courseID}"
    result = requests.get(url, headers=authHeader)
    if len(result.text) > 2:
        courseInfo = json.loads(result.text)
        undeletedIDs.append([courseInfo[0]['id'], courseInfo[0]['sis_import_id'], courseInfo[0]['sis_course_id'], courseInfo[0]['workflow_state'], courseInfo[0]['name']])
#
if len(undeletedIDs) > 0:
    table = columnar(undeletedIDs, columnHeaders, no_borders=True)
    print()
    print('>>> These courses are deleted in SRA but remain in Canvas <<<')
    print()
    print(table)
    print()
