#!/usr/bin/python
#
import sys, requests, os, csv
from pprint import pprint
from PyPDF2 import PdfReader
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import logScriptStart, realm
# Initialize environment
#logScriptStart()
realm = realm()
canvasToken = realm["canvasToken"]
canvasApi = realm["canvasApi"]
headers = {"Authorization": f"Bearer {canvasToken}"}
params = {"per_page": 100}
print()
bannerTerm = input("Enter Banner Term (e.g., 120255): ")
print()
targetDir = '/var/lib/canvas-mgmt/tmp/pdf/'
rCsvFile = f'/var/lib/canvas-mgmt/tmp/pdf/{bannerTerm}_canvas-pdf-pages.csv'    #results file
sCsvFile = f'/var/lib/canvas-mgmt/tmp/pdf/{bannerTerm}_canvas-pdf-list.csv'     #source file
print(f'targetDir: {targetDir}')
print(f'rCsvFile:  {rCsvFile}')
print(f'sCsvFile:  {sCsvFile}')
print()
#
def download_pdf(url, targetFilePath):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(targetFilePath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
#
if not os.path.exists(sCsvFile):
    print(f"Source file {sCsvFile} does not exist. Exiting...")
    sys.exit(1)
#
with open(rCsvFile, 'w', newline='') as resultsCsvFile:
    fieldnames = ['numPages', 'totalSize', 'uiucCourseID', 'attachmentID', 'pdfName']
    writer = csv.DictWriter(resultsCsvFile, fieldnames=fieldnames)
    writer.writeheader()
    with open(sCsvFile, 'r', newline='') as sourceCsvFile:
        csvFile = csv.DictReader(sourceCsvFile, delimiter='|')
        for row in csvFile:
            print(row)
            attachmentID = row['id']
            uiucCourseID = row['sis_source_id']
            pdfName = row['display_name']
            pdfURL = row['download_url']
            totalSize = row['size_kb']
            targetFilePath = f'{targetDir}{uiucCourseID}-{attachmentID}.pdf'
            try:
                r = download_pdf(pdfURL, targetFilePath)
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