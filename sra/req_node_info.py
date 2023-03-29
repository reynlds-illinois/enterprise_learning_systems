import cx_Oracle, sys
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
from canvasFunctions import chooseEnv
from columnar import columnar
#logScriptStart()
#
realm = chooseEnv()
dbUser = realm['sraDbUser']
dbPass = realm['sraDbPass']
dbHost = realm['sraDbHost']
dbPort = realm['sraDbPort']
dbSid = realm['sraDbSid']
envLabel = realm['envLabel']
print('')
#
print(f"Connected to:  {dbHost}:{dbPort}")
print('')
#
columnHeaders = ['level','name','short_name','code','node_id']
unitQuery = '''SELECT bn."LEVEL",bn."NAME",bn.SHORT_NAME,bn.CODE,bn.NODE_ID
               FROM CORREL.T_BB9_NODE bn
               WHERE bn."LEVEL" = 1'''
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
#
cursor.execute(unitQuery)
allUnits = cursor.fetchall()
#
combinedHeader = ['level', 'short_name', 'name', 'code', 'node_id', 'parent_node']
combined = []
for row in allUnits:
    combined.append([row[0], f'{row[2]}', row[1], row[3], row[4], '----'])
    parentNode = row[4]
    deptQuery = f'''SELECT bn."LEVEL",bn."NAME",bn.SHORT_NAME,bn.CODE,bn.NODE_ID,bn.parent_node_id
               FROM CORREL.T_BB9_NODE bn
               WHERE bn."LEVEL" = 2 AND bn.parent_node_id = {parentNode}'''
    cursor.execute(deptQuery)
    dept = cursor.fetchall()
    for row in dept:
        combined.append([row[0], f'    {row[2]}', row[1], row[3], row[4], row[5]])
#
fullTable = columnar(combined, combinedHeader, no_borders=True)
print(fullTable)
print('')
