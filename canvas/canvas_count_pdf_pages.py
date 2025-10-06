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
targetDir = '/var/lib/canvas-mgmt/tmp/pdf/'
rCsvFile = '/var/lib/canvas-mgmt/tmp/canvas-pdf-pages.csv'
sCsvFile = '/var/lib/canvas-mgmt/tmp/canvas-pdf-list.csv'
#
def downloadPDF(url, targetFilePath):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(targetFilePath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
#
with open(rCsvFile, 'w', newline='') as resultsCsvFile:
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
            targetFilePath = f'{targetDir}-{uiucCourseID}-{attachmentID}.pdf'
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