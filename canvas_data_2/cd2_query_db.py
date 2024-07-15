import os, psycopg2, sys, argparse, json, csv, datetime
sys.path.append("/var/lib/canvas-mgmt/bin")
from pprint import pprint
from canvasFunctions import getEnv
from canvasFunctions import logScriptStart
from columnar import columnar
envDict = getEnv()
logScriptStart()
print('')
pgHost = envDict['cd2.pg.host']
pgPass = envDict['cd2.pg.pass']
pgUser = envDict['cd2.pg.user']
pgDb = envDict['cd2.pg.db']
pgPort = envDict['cd2.pg.port']
nextAction = ''
results = ''
try:
    pgConn = psycopg2.connect(host=pgHost,database=pgDb,user=pgUser,password=pgPass)
    pgCursor = pgConn.cursor()
    print('> Connected to Canvas Data 2 Postgres.')
    print('')
except:
    print('> Cannot connect to Postgres at this time.')
    print('')
print("> Enter your query. NOTE: a semi-colon must be on the last line by itself.")
print('')
buffer = []
while True:
    line = input()
    if line == ";":
        break
    buffer.append(line)
pgQuery = "\n".join(buffer)
print('')
print('> Running query...')
print('')
pgCursor.execute(pgQuery)
columnHeaders = list([desc[0] for desc in pgCursor.description])
results = pgCursor.fetchall()
if len(results) >= 1:
    print('|=============================================')
    print(f'| Total records returned: {len(results)}')
    print('|=============================================')
    print('')
    while nextAction != 'a' and nextAction != 'f' and nextAction != 'e' and nextAction != 'q':
        nextAction = input('show (a)ll records, show (f)irst 10 records, (e)xport to CSV, (q)uit: ').strip().lower()
    print('')
    if nextAction == 'a':
        listResults = []
        for row in results:
            listResults.append([row])
        fullResultsTable = columnar(listResults, columnHeaders, no_borders=True)
        print(fullResultsTable)
    elif nextAction == 'e':
        print('|=============================================')
        print('| Exporting to CSV...')
        now = datetime.datetime.now().timestamp()
        targetFile = f'/var/lib/canvas-mgmt/reports/cd2_query_{now}.csv'
        with open(targetFile, 'w') as exportFile:
            write = csv.writer(exportFile, delimiter='|')
            write.writerow(columnHeaders)
            write.writerows(results)
            print(f'| CSV export file: {targetFile}')
            print('|=============================================')
            print('')
    elif nextAction == 'f':
        counter = 0
        listResults = []
        while counter < 10:
            for row in results:
                listResults.append([row])
                counter += 1
        resultsTable = columnar(listResults, columnHeaders, no_borders=True)
        print(resultsTable)
    else:
        print('')
        print('Exiting...')
else:
    print('|=============================================')
    print('| NO RECORDS RETURNED...EXITING...')
    print('|=============================================')
    print()
pgCursor.close()
print('')
