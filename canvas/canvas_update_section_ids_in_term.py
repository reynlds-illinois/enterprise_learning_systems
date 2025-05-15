#!/usr/bin/python
#
import sys, requests, json, time, csv
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import realm
from canvasFunctions import getEnv
from columnar import columnar

# Initialize realm
env = getEnv()
realm = realm()
bannerTerm = ''
sectionsUpdated = []
sectionUpdateFailed = []
sectionsSkipped = []
skippedHeader = ['canvas_section_id', 'section_id', 'canvas_course_id', 'course_id', 'name']

# Canvas API setup
canvasApi = realm['canvasApi']
canvasToken = realm['canvasToken']
bannerTerms = env['banner.terms'].split(",")
authHeader = {"Authorization": f"Bearer {canvasToken}"}
print(f'Connected to: {canvasApi}')
print()

# File paths for the two CSV files
canvasCoursesCSV = "/var/lib/canvas-mgmt/config/canvas_courses.csv"
canvasSectionsCSV = "/var/lib/canvas-mgmt/config/canvas_sections.csv"

# Function to load a CSV file into a list of lists
def csv2List(filepath):
    data = []
    with open(filepath, mode="r", newline="", encoding="utf-8") as csvFile:
        reader = csv.reader(csvFile)
        for row in reader:
            data.append(row)
    return data

# Load the two CSV files
canvasCourses = csv2List(canvasCoursesCSV)
canvasSections = csv2List(canvasSectionsCSV)

while bannerTerm not in bannerTerms:
    bannerTerm = input("Enter the Banner term (e.g., 120251): ")
    print()

for course in canvasCourses:
    if course[8] == bannerTerm:
        #print(f'COURSE: {course}')
        canvasCourseID = course[0]
        uiucCourseID = course[1]
        for section in canvasSections:
            if section[3] == uiucCourseID:
                if len(section[1]) > 0:
                    #print(f'SECTION: {section}')
                    canvasSectionID = section[0]
                    uiucSectionID = section[1]
                    sectionName = section[5]
                    sectionRubric = section[1].split("_")[0]
                    sectionNumber = section[1].split("_")[1]
                    sectionDesignator = section[1].split("_")[2]
                    sectionSpaceID = section[1].split("_")[3]
                    sectionCRN = sectionName.split("CRN")[-1].strip()
                    updatedUiucSectionID = f"{sectionRubric}_{sectionNumber}_{sectionDesignator}_{bannerTerm}_{sectionCRN}_{sectionSpaceID}"
                    sectionParams = {'course_section[sis_section_id]': updatedUiucSectionID}
                    sectionUpdateURL = f'{canvasApi}sections/{canvasSectionID}'
                    #print(f'sectionUpdateURL: {sectionUpdateURL}')
                    response = requests.put(sectionUpdateURL, headers=authHeader, params=sectionParams)
                    if response.status_code == 200:
                        print(f"Updated section {uiucSectionID} with new SIS ID: {updatedUiucSectionID}")
                        sectionsUpdated.append([uiucSectionID, updatedUiucSectionID])
                    else:
                        print(f"Failed to update section {uiucSectionID}: {response.status_code} - {response.text}") 
                        sectionUpdateFailed.append([uiucSectionID, updatedUiucSectionID, response.status_code, response.text])
                    #input("Press Enter to continue...")
                    #time.sleep(1)
                else:
                    #print(f"Skipping section {section[1]} for course {uiucCourseID} as it does not match the Banner term {bannerTerm}")
                    sectionsSkipped.append([section[0], section[1], section[2], section[3], section[5]])

print()
if len(sectionUpdateFailed) > 0:
    print("The following sections failed to update:")
    print(columnar(sectionUpdateFailed, no_borders=True))
    print()
    if len(sectionsSkipped) > 0:
        #print(f'sectionsSkipped: {len(sectionsSkipped)}')
        print("The following sections were skipped:")
        print(columnar(sectionsSkipped, skippedHeader))
else:
    print("All sections updated successfully.")
    print()
    #print(columnar(sectionsUpdated, headers=["Canvas Section ID", "Updated SIS ID"], no_borders=True))
    print(f"Total sections updated: {len(sectionsUpdated)}")
    #print(f"Total sections failed to update: {len(sectionUpdateFailed)}")
    print()
    if len(sectionsSkipped) > 0:
        #print(f'sectionsSkipped: {len(sectionsSkipped)}')
        print("The following sections were skipped:")
        print(columnar(sectionsSkipped, skippedHeader, no_borders=True))
    print()
