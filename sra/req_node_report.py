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
#logScriptStart()
realm = realm()
#
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

    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to download the Excel file. {e}")
        return []
    except Exception as e:
        print(f"Error: An unexpected error occurred. {e}")
        return []
#
def sraGetNodes(cursor):
    sraAllNodes = []
    sraNodeQuery = '''SELECT bn.NODE_ID, bn.CODE, bn.SHORT_NAME, bn."NAME", bn."LEVEL", bn.PARENT_NODE_ID
                      FROM CORREL.T_BB9_NODE bn'''
    cursor.execute(sraNodeQuery)
    sraAllNodes = cursor.fetchall()
    return sraAllNodes
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
def compareDmi2Sra(dmiTargetList, sraAllNodes):
    notInSRA = []
    for row in dmiTargetList[1:]:
        #print(row)
        if not any(e[3] == row[0] for e in sraAllNodes):
            tempName = str(row[0].replace("&#39;","'"))
            deptCode = str(f"{row[1]}{row[3]}")
            if not row[2]:
                college = "-NA-"
            else:
                college = str(row[2])
            notInSRA.append([tempName, row[1], college, row[3], deptCode, row[4]])
    return notInSRA
#
dmiTargetList = dmiGetInfo()
pprint(dmiTargetList)
sraAllNodes = sraGetNodes(cursor)
pprint(sraAllNodes)
notInSRA = compareDmi2Sra(dmiTargetList, sraAllNodes)
#
print("These departments are in DMI data, but are NOT found in the SRA database:")
print(columnar(notInSRA, dmiTargetListHeader, no_borders=True))
print('')
