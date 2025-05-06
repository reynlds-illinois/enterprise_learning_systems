#!/usr/bin/python
#
import sys, csv, requests
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import logScriptStart
from canvasFunctions import realm
from columnar import columnar
import pandas as pd
from io import BytesIO
from io import StringIO
from sqlalchemy import create_engine
from sqlalchemy import text
#
logScriptStart()
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
deptsMissingInSra = []
addContinue = 'y'
url = 'https://www.dmi.illinois.edu/ddd/mktext.asp'
listHeader = ['BANNER_ORG', 'PARENT_ACCT', 'PARENT_SHORT', 'PARENT_ID', 'NEW_ACCT', 'DEPT_NAME', 'PARENT_NAME', 'CODE_EXISTS']
#
def connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid):
    """
    Create a connection to a SQL database using SQLAlchemy.
    """
    try:
        # Create the database URL for SQLAlchemy
        db_url = f"oracle+cx_oracle://{dbUser}:{dbPass}@{dbHost}:{dbPort}/?service_name={dbSid}"
        # Create the SQLAlchemy engine
        engine = create_engine(db_url)
        # Establish a connection
        connection = engine.connect()
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
#
def fetchDeptInfo(url):
    """
    Fetches TSV data from a given URL and parses it into a Python list.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        tsvContent = response.text
        tsvReader = csv.reader(StringIO(tsvContent), delimiter='\t')
        tsvData = [row for row in tsvReader]
        return tsvData
    except requests.exceptions.RequestException as e:
        print(f"Error fetching TSV data: {e}")
        return []
#
def sraGetNodes(connection):
    """
    Fetches all nodes from the CORREL.T_BB9_NODE table.
    """
    sraNodeQuery = text('''SELECT bn.NODE_ID, bn.CODE, bn.SHORT_NAME, bn."NAME", bn."LEVEL", bn.PARENT_NODE_ID
                           FROM CORREL.T_BB9_NODE bn''')
    result = connection.execute(sraNodeQuery)
    sraAllNodes = result.fetchall()
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
def deptCompare(deptInfo, sraNodes):
    """
    Identifies rows present in fetchDeptInfo but not in sraGetNodes
    """
    notInSra = []
    sraElements = {node[3] for node in sraNodes}  # Extract the fourth element from sraGetNodes
    for row in deptInfo:
        if len(row) > 2:  # Ensure the row has at least three elements
            if row[2] not in sraElements:  # Compare the third element from fetchDeptInfo
                notInSra.append(row)
    return notInSra
#
def add_node_to_database(connection, newNodeID, newCode, newShortName, deptName, parentNodeID):
    """
    Adds a new node to the database if codeExists = 'NO'.
    """
    try:
        # Define the SQL query for the insert
        insertQuery = text('''
            INSERT INTO correl.T_BB9_NODE (NODE_ID, CODE, SHORT_NAME, NAME, "LEVEL", PARENT_NODE_ID)
            VALUES (:node_id, :ncode, :short_name, :rname, :level, :parent_node_id)
        ''')
        # Execute the insert query
        connection.execute(insertQuery, {
            "node_id":newNodeID,
            "ncode": newCode,
            "short_name": newShortName,
            "rname": deptName,
            "level": "2",
            "parent_node_id": parentNodeID
        })
        connection.commit()  # Commit the transaction
        print(f"Node with CODE '{newCode}' successfully added to the database.")
    except Exception as e:
        print(f"Error adding node to the database: {e}")
#
# Establish the database connection
connection = connect2Sql(dbUser, dbPass, dbHost, dbPort, dbSid)

# Fetch data from the database
dmiDeptInfo = fetchDeptInfo(url)
sraAllNodes = sraGetNodes(connection)

# Compare the data
notInSRA = deptCompare(dmiDeptInfo, sraAllNodes)

# Process the results
for item in notInSRA[1:]:
    currentAcctCode = item[1]
    firstChar = currentAcctCode[0]
    lastElement = currentAcctCode.split('-')[-1]
    parentNode = currentAcctCode.split('-')[1]
    newCode = f"{firstChar}{lastElement}"

    # Use a parameterized query to check if newCode exists
    newAcctCodeQuery = text("SELECT COUNT(*) FROM correl.T_BB9_NODE WHERE CODE = :new_code")
    newAcctResult = connection.execute(newAcctCodeQuery, {"new_code": newCode}).scalar()
    if newAcctResult > 0:
        codeExists = 'YES'
    else:
        codeExists = 'NO'

    parentAcctQuery = text("SELECT SHORT_NAME FROM correl.T_BB9_NODE WHERE CODE = :parent_node")
    parentAcct = connection.execute(parentAcctQuery, {"parent_node": parentNode}).scalar()
    parentAcctQuery = text("SELECT NODE_ID FROM correl.T_BB9_NODE WHERE CODE = :parent_node")
    parentNodeID = connection.execute(parentAcctQuery, {"parent_node": parentNode}).scalar()

    deptsMissingInSra.append([item[1], parentNode, parentAcct, parentNodeID, newCode, item[2], item[27], codeExists])

    # If codeExists = 'NO', prompt the user to add the node
# Sort the results by the last column (CODE_EXISTS) in ascending order
deptsMissingInSra = sorted(deptsMissingInSra, key=lambda x: x[-1])

# Print the sorted results
print("These departments are in DMI data, but are NOT found in the SRA database:")
print(columnar(deptsMissingInSra, listHeader, no_borders=True))
print('')

for item in deptsMissingInSra:
    yesNo = ''
    addContinue = ''
    if item[7] == 'NO':
        # Prompt the user to add the node to the database
        print(columnar([item], listHeader, no_borders=True))
        print()
        while yesNo not in ['y', 'n']:
            yesNo = input(f"= Do you want to add this node to the database? (y/n): ").strip().lower()
            print()
        if yesNo == 'y':
            while True:
                newNodeID = input(f"  = Enter NODE_ID for the new node with CODE '{item[4]}': ").strip()
                print()
                # Check if newNodeID already exists in sraAllNodes
                if any(str(node[0]) == newNodeID for node in sraAllNodes):  # Cast node[0] to string
                    print(f"  ! NODE_ID '{newNodeID}' already exists in the database. Please enter a unique NODE_ID.")
                    print()
                else:
                    break  # Exit the loop if the newNodeID is unique
            newCode = item[4]
            newShortName = input(f"  = Enter SHORT_NAME for the new node with CODE '{newCode}': ").strip()
            deptName = item[5]
            currentAcctCode = item[1]
            deptLevel = 2
            parentNodeID = item[3]
            try:
                addContinue = input(f"  > Do you want to add this node to the database? (y/n): ").strip().lower()
                print()
            except Exception as e:
                print(f"Error: {e}")
                addContinue = 'n'
            if addContinue == 'y':
                # Call the function to add the node to the database
                add_node_to_database(connection, newNodeID, newCode, newShortName, deptName, parentNodeID)
                sraAllNodes = sraGetNodes(connection)
                print()