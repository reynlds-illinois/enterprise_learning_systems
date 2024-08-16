#
#!/usr/bin/python
#
import cx_Oracle, sys, argparse, requests, json, csv
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
from canvasFunctions import canvasGetAccountID
from canvasFunctions import findCanvasCourse
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
deptList = []
canvasNewDept = ''
yesNo = ''
print()
print(">>> NOTE:  this is for REGISTRAR-ENABLED courses only!!!")
print()
#
try:
    cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
    print(f"Connected to:  {dbHost}:{dbPort}")
    print(f"               {canvasApi}")
    print('')
except Exception as e:
    print(f"> Error: {e}")
    print()
#
with open('/var/lib/canvas-mgmt/config/canvas_accounts.csv', 'r') as departments:
    deptReader = csv.reader(departments)
    deptList = []
    for line in deptReader:
        temp = line[1].split('_',1)[0]
        if temp == 'DEPT':
            deptList.append(line[1])
#
spaceID = input("Enter the 6-digit space ID:  ")
#
spaceQuery = f"""SELECT tsr.TARGET_PRODUCT_KEY || '_' || tsr.SPACE_ID AS COURSE_ID,
                   tt.BANNER_TERM, 'DEPT_' || tbn.SHORT_NAME AS DEPT,
                   'UNIT_' || (SELECT tbn2.short_name FROM correl.T_BB9_NODE tbn2 WHERE tbn2.node_id = tbn.PARENT_NODE_ID) AS UNIT
                 FROM correl.T_SPACE_REQUEST tsr
                   JOIN correl.T_TERM tt ON tt.TERM_ID = tsr.TERM_ID
                   JOIN correl.T_BB9_SPACE_NODE tbsn ON tbsn.SPACE_ID = tsr.SPACE_ID
                   JOIN correl.T_BB9_NODE tbn ON tbn.NODE_ID = tbsn.NODE_ID
                 WHERE tsr.SPACE_ID = '{spaceID}'"""
#
spaceInfo = []
cursor.execute(spaceQuery)
queryResult = cursor.fetchall()
for item in queryResult[0]:
    spaceInfo.append(item)
#
if len(spaceInfo) == 4:
    courseID = spaceInfo[0]
    termID = spaceInfo[1]
    sourceSraDeptAcct = spaceInfo[2]
    sourceSraUnitAcct = spaceInfo[3]
    canvasCourseID = findCanvasCourse(courseID)
#
canvasCourseUrl = f"{canvasApi}courses/{canvasCourseID}"
canvasCourseInfo = requests.get(f"{canvasApi}courses/{canvasCourseID}", headers=authHeader).json()
sourceCanvasAcct = requests.get(f"{canvasApi}accounts/{canvasCourseInfo['account_id']}",headers=authHeader).json()
#
while canvasNewDept not in deptList:
    print()
    print("=== Enter the new DEPT location for the course below.")
    print("=== NOTE:  do NOT use the 'DEPT_' prefix!")
    print()
    sraNewDept = input(">>> ").upper()
    canvasNewDept = f"DEPT_{sraNewDept}"
    print()
#
sraTargetAcctQuery = f"""SELECT *
                         FROM correl.T_BB9_NODE tbn
                         WHERE tbn.SHORT_NAME = '{sraNewDept}'
                           AND tbn.PARENT_NODE_ID IS NOT NULL"""
cursor.execute(sraTargetAcctQuery)
sraTargetAcctResult = cursor.fetchall()
sraTargetAcct = []
for item in sraTargetAcctResult[0]:
    sraTargetAcct.append(item)
targetParentNodeID = sraTargetAcct[5]
#
if len(sraTargetAcct) == 7:
    targetNodeID = int(sraTargetAcct[0])
    targetCode = sraTargetAcct[1]
    targetShortName = sraTargetAcct[2]
    targetName = sraTargetAcct[3]
    targetCanvasAcct = f"DEPT_{targetShortName}"
    spaceID = int(spaceID)
#
print("|=== Current Course/Account Info ===")
print("|")
print(f"| Course ID:    {courseID}")
print(f"| CourseName:   {canvasCourseInfo['name']}")
print(f"| Term ID:      {termID}")
print()
print("|=== Proposed Changes ===")
#print(f"| Current Parent Unit:  {sourceSraUnitAcct}")
print("|")
print(f"| Moving from Current Dept: {sourceSraDeptAcct} to {targetCanvasAcct}")
print()
#print(f"> targetNodeID: {targetNodeID}")
#print(f"> spaceID:      {spaceID}")
#print()
while yesNo != 'y' and yesNo != 'n':
    yesNo = input(">>> Continue (y/n)? ").lower()[0]
    print()
if yesNo == 'n':
    print()
    print("No changes made...Exiting...")
    print()
else:
    try:
        targetCanvasAcctID = canvasGetAccountID(targetCanvasAcct)
        targetCanvasAcctParams = {"course[account_id]":targetCanvasAcctID}
        targetCanvasAcctUrl = f"{canvasApi}courses/{canvasCourseID}"
        #
        moveCanvasCourse = requests.put(targetCanvasAcctUrl, headers=authHeader, params=targetCanvasAcctParams)
        print("=== Course successfully moved in Canvas!")
        print()
        #
        sraCourseUpdate1 = f"""UPDATE correl.T_BB9_SPACE_NODE tbsn
                                   SET tbsn.NODE_ID = {targetNodeID}
                                   WHERE tbsn.SPACE_ID = {spaceID}"""
        sraCourseUpdate2 = f"""UPDATE correl.T_BB9_SPACE_REQUEST tbsr
                               SET tbsr.PRIMARY_DEPARTMENT_KEY = {targetCode}
                               WHERE tbsr.SPACE_REQUEST_PTR_ID = {spaceID}"""
        cursor.execute(sraCourseUpdate1)
        cursor.execute(sraCourseUpdate2)
        cursor.execute('COMMIT')
        print("=== course successfully updated in SRA!")
        print()
        print(">>> All changes successfully made...Exiting...")
        print()
    except Exception as e:
        print(f"Exception of one or more errors:  {e}")
        print()
print()
