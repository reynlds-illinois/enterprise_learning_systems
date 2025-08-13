#!/usr/bin/python
#
import cx_Oracle, sys, csv, requests
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import getEnv
from canvasFunctions import connect2Sql
from canvasFunctions import logScriptStart
from canvasFunctions import realm
from columnar import columnar
import pandas as pd
from io import BytesIO
#
realm = realm()
#
#logScriptStart()
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
dbUser = realm['sraDbUser']
dbPass = realm['sraDbPass']
dbHost = realm['sraDbHost']
dbPort = realm['sraDbPort']
dbSid = realm['sraDbSid']
envLabel = realm['envLabel']
cursor = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)
addContinue = 'y'
dmiTargetListHeader = ['DEPTNAME', 'DEPTTYPE', 'COLLEGE_CODE', 'C_DEPT', 'NEW_DEPT_CODE', 'COLLNAME']
#
def dmiGetInfo():
    """
    Downloads an Excel file from a public website, processes it, and converts it into a list of lists.
    """
    try:
        # Download the Excel file
        url = 'https://www.dmi.illinois.edu/ddd/mkexcel.aspx?role=0&roleDesc=Execute%20Officer'
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        # Wrap the response content in a BytesIO object
        excel_data = pd.read_excel(BytesIO(response.content))
        # Convert the DataFrame to a CSV-like string and split it into lines
        csv_data = excel_data.to_csv(index=False, header=True, encoding='utf-8', sep='|')
        csv_lines = csv_data.splitlines()
        # Parse the CSV lines into a list of lists
        dmiTempList = [line.split('|') for line in csv_lines]
        # Process the data to extract the required fields
        dmiTargetList = []
        for row in dmiTempList[1:]:  # Skip the header row
            #pprint(row)
            try:
                c_deptTemp = row[17].split('-')[-1] if len(row) > 17 else ''
                dmiTargetList.append([
                    row[0].strip() if len(row) > 0 else '',
                    row[9] if len(row) > 9 else '',
                    row[15] if len(row) > 15 else '',
                    c_deptTemp,
                    row[18].strip() if len(row) > 18 else ''
                ])
            except IndexError:
                # Handle rows with missing data
                print(f"Warning: Skipping row due to missing data: {row}")
                continue
        return dmiTargetList
    except:
        print("Error: An unexpected error occurred while fetching DMI information.")
        return []
#
def sraGetNodes(cursor):
    sraAllNodes = []
    sraTemp = []
    sraNodeQuery = '''SELECT bn.NODE_ID, bn.CODE, bn.SHORT_NAME, bn."NAME", bn."LEVEL", bn.PARENT_NODE_ID
                      FROM CORREL.T_BB9_NODE bn'''
    cursor.execute(sraNodeQuery)
    sraHeaders = [row[0] for row in cursor.description]
    sraTemp.extend([sraHeaders])
    sraAllNodes = cursor.fetchall()
    for row in sraAllNodes:
        sraTemp.extend([list(row)])
    return sraTemp
#
def canvasAccts(canvasApi, canvasToken):
    canvasP = []
    canvasC = []
    canvasAll = []
    headers = {"Authorization": f"Bearer {canvasToken}"}
    params = {"per_page": 100}
    url = f'{canvasApi}accounts/1/sub_accounts'
    response = requests.get(url, headers=headers, params=params)
    canvasP = response.json()
    while 'next' in response.links:
        response = requests.get(response.links['next']['url'], headers=headers, params=params)
        canvasP.extend(response.json())
    for acct in canvasP:
        #canvasAll.extend(acct)
        #print(acct)
        url = f"{canvasApi}accounts/{acct['id']}/sub_accounts"
        #print(url)
        response = requests.get(url, headers=headers, params=params)
        #print(response).json()
        canvasC.extend(response.json())
        while 'next' in response.links:
            response = requests.get(response.links['next']['url'], headers=headers, params=params)
            canvasC.extend(response.json())
    for row in canvasP:
        canvasAll.extend([row])
    for row in canvasC:
        canvasAll.extend([row])
    return canvasAll
#
dmi = dmiGetInfo()
sra = sraGetNodes(cursor)
canvas = canvasAccts(canvasApi, canvasToken)
#
resultsHeader = ['code', 'short_name', 'sis_id', 'name', 'in_canvas', 'in_dmi']
resultsList = []
for row in sra[1:]:
    if row[4] == 2:
        tempAcct = f"DEPT_{row[2]}"
    else:
        tempAcct = f"UNIT_{row[2]}"
    if len(list(filter(lambda row: row['sis_account_id'] == tempAcct, canvas))) == 1:
        inCanvas = 'YES'
    else: inCanvas = 'NO'
    temp = str(row[1])
    if len(list(filter(lambda row: row[3] == temp, dmi))) == 1:
        inDmi = 'YES'
    else:
        inDmi = 'NO'
    resultsList.append([row[1], row[2], tempAcct, row[3], inCanvas, inDmi])
#
print(columnar(resultsList, resultsHeader, no_borders=True))
print()
