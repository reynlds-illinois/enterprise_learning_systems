#!/usr/bin/python
#
import sys, requests, os, csv,  datetime
from pprint import pprint
from PyPDF2 import PdfReader
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import logScriptStart, realm, getEnv, connect2SQL
#logScriptStart()
envDict = getEnv()
realm = realm()
bannerTerm = ''
canvasToken = realm["canvasToken"]
canvasApi = realm["canvasApi"]
now = datetime.datetime.now().timestamp()
targetDir = '/var/lib/canvas-mgmt/tmp/pdf/'
rCsvFile = f'/var/lib/canvas-mgmt/tmp/{now}_canvas-pdf-pages.csv'
sCsvFile = f'/var/lib/canvas-mgmt/tmp/{now}_canvas-pdf-list.csv'
bannerTerms = envDict['banner.terms']
print()
while bannerTerm not in bannerTerms:
    bannerTerm = input('Enter the Banner term: ')
    print()
print()
allPDFsFile = f'/var/lib/canvas-mgmt/tmp/pdf/{now}_all_pdfs_{bannerTerm}.csv'
#
def getAllPDFs(envDict, now, bannerTerm, allPDFsFile):
    print()
    print(f'  > querying CD2 for PDFs in Banner Term: {bannerTerm}')
    print()
    allPDFs = []
    pgHost = envDict['cd2.pg.host']
    pgPass = envDict['cd2.pg.pass']
    pgUser = envDict['cd2.pg.user']
    pgDb = envDict['cd2.pg.db']
    pgPort = envDict['cd2.pg.port']
    pgConn = connect2SQL(pgUser, pgPass, pgHost, pgPort, pgDb)
    pgCursor = pgConn.cursor()
    #print('> Connected to Canvas Data 2 Postgres.')
    #headers = {"Authorization": f"Bearer {canvasToken}"}
    #params = {"per_page": 100}
    sqlQuery = f"""select c.sis_source_id, f.name, a.id, a.workflow_state, a.file_state, (a.size / 1024) as size_KB, a.display_name, 'https://canvas.illinois.edu/files/' || a.id || '/download?download_frd=1&verifier=' || a.uuid as DOWNLOAD_URL
    from canvas.attachments a 
    join canvas.courses c on c.id = a.context_id
    join canvas.enrollment_terms et on et.id = c.enrollment_term_id
    join canvas.folders f on f.id = a.folder_id  
    where a.content_type = 'application/pdf'
    and a.context_type = 'Course'
    and c.sis_source_id is not null
    and et.sis_source_id = '{bannerTerm}'
    and a.file_state != 'deleted'
    order by c.sis_source_id asc, a.display_name asc;"""
    #
    pgCursor.execute(sqlQuery)
    #columnHeaders = list([desc[0] for desc in pgCursor.description])
    results = pgCursor.fetchall()
    for row in results:
        allPDFs.append([row])
    with open(allPDFsFile, 'w') as exportFile:
        write = csv.writer(exportFile, delimiter='|')
        #write.writerow(columnHeaders)
        write.writerows(results)
#
def downloadPDF(url, targetFilePath):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(targetFilePath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
#
getAllPDFs(envDict, now, bannerTerm, allPDFsFile)
with open(allPDFsFile, 'w', newline='') as resultsCsvFile:
    fieldnames = ['numPages', 'totalSize', 'uiucCourseID', 'attachmentID', 'pdfName']
    writer = csv.DictWriter(resultsCsvFile, fieldnames=fieldnames)
    writer.writeheader()
    with open(sCsvFile, 'r', newline='') as sourceCsvFile:
        csvFile = csv.reader(sourceCsvFile)
        for row in csvFile:
            print(row)
            attachmentID = row[2]
            uiucCourseID = row[0]
            pdfName = row[6]
            pdfURL = row[7]
            totalSize = row[5]
            targetFilePath = f'{targetDir}{uiucCourseID}-{attachmentID}.pdf'
            try:
                r = downloadPDF(pdfURL, targetFilePath)
                with open(targetFilePath, 'rb') as f:
                    reader = PdfReader(f)
                    totalPages = len(reader.pages)
                    writer.writerow({'numPages': totalPages, 'totalSize': totalSize,'uiucCourseID': uiucCourseID, 'attachmentID': attachmentID, 'pdfName': pdfName})
                f.close()
                os.remove(targetFilePath)
            except Exception as e:
                print(f"Error downloading {pdfURL}: {e}")
            print()
            #input('Enter to continue...')
            #print()