#!/usr/bin/python
#
import sys, requests, json
from pprint import pprint
from bs4 import BeautifulSoup
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import findCanvasCourse
from columnar import columnar

# Initialize realm
realm = realm()

# Canvas API setup
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
params = {"per_page": 100}
authHeader = {"Authorization": f"Bearer {canvasToken}"}
reportsPath = '/var/lib/canvas-mgmt/reports/'
uiucCourseID = ''

# Get course ID from user
while uiucCourseID == '':
    uiucCourseID = input('Please enter the course ID:  ')
    print()
canvasCourseID = findCanvasCourse(uiucCourseID)

url = f'{canvasApi}courses/{canvasCourseID}?include[]=syllabus_body'

r = requests.get(url, headers=authHeader)

r = r.json()

syllabusBodyHTML = r.get('syllabus_body', None)
if not syllabusBodyHTML:
    print("Error: 'syllabus_body' not found in the response.")
    sys.exit(1)

soup = BeautifulSoup(syllabusBodyHTML, 'html.parser')
stylesheetLink = soup.find('link', rel='stylesheet')['href'] if soup.find('link', rel='stylesheet') else None
downloadLink = soup.find('a', class_='btn')['href'] if soup.find('a', class_='btn') else None
scriptSrc = soup.find('script', src=True)['src'] if soup.find('script', src=True) else None

# Construct the JSON object
syllabusJSON = {
    "stylesheet_link": stylesheetLink,
    "download_link": downloadLink,
    "script_src": scriptSrc,
    "text_content": soup.get_text(strip=True),  # Extract plain text content
    "html_content": syllabusBodyHTML,           # Original HTML content
    "element_count": len(soup.find_all()) }     # Count of HTML elements

downloadLink = syllabusJSON['download_link']

# Transform the download link to the desired format
if downloadLink:
    # Extract the file ID from the original link
    fileID = downloadLink.split("preview=")[-1] if "preview=" in downloadLink else None
    if fileID:
        try:
            # Construct the new download link
            downloadLink = f"https://illinoisedu.beta.instructure.com/files/{fileID}/download?download_frd=1"
            syllabusJSON["download_link"] = downloadLink  # Update the JSON object
            #
            response = requests.get(downloadLink, headers=authHeader, stream=True)
            response.raise_for_status()  # Raise an error for bad responses
            #
            # Define the local file name
            localFilename = f"{reportsPath}syllabus-{uiucCourseID}-{fileID}.pdf"
            #
            # Write the file to the local machine
            with open(localFilename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                    file.write(chunk)
            #
            print(f"File downloaded successfully as {localFilename}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading the file: {e}")
print()