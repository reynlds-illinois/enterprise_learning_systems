#!/usr/bin/python
#
import os, sys, time, base64
from pprint import pprint
sys.path.append("/var/lib/canvas-mgmt//bin")
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from boxsdk import JWTAuth, Client
from boxsdk.exception import BoxAPIException
from boxsdk.object.collaboration import CollaborationRole
from canvasFunctions import realm
from canvasFunctions import getEnv
from canvasFunctions import canvasGetUserInfo
from canvasFunctions import findCanvasCourse

env = getEnv()
realm = realm()
canvasURL = realm['canvasUrl']
jwtAuthFile = env['uofi.box.jwtauth.file']
canvasUser = env['cm.user']
canvasPass = env['cm.pass']
canvasAuthURL = f'{canvasURL}/login/canvas'
print(f'canvasAuthURL: {canvasAuthURL}')
print()
boxJwtAuthFile = env['uofi.box.jwtauth.file']
boxAuth = JWTAuth.from_settings_file(boxJwtAuthFile)
boxClient = Client(boxAuth)
boxParentFolderID = env['uofi.box.tdx.parent.folder']
boxRequstorRole = 'Viewer'
reportsPath = '/var/lib/canvas-mgmt/reports/'
yesNo = ['y', 'n']

tdxTicket = input('  > Enter TDX ticket: ')
print()
requestorNetID = input('  > Enter the NetID of the TDX requestor: ')
print()
netID = input    ("  > Enter the student's NetID: ")
canvasUserID = canvasGetUserInfo(netID)[0]
print()
courseID = input ('  > Enter the Course ID : ')
canvasCourseID = findCanvasCourse(courseID)
print()
#
input('  > Press Enter to continue... ')
#print()

# Set up the report URL and file name
reportURL = f'{canvasURL}/courses/{canvasCourseID}/users/{canvasUserID}/usage'
targetFileName = f'tdx_{tdxTicket}_access_report.pdf'
targetFilePath = f'{reportsPath}{targetFileName}'
requestorEmailAddress = f'{requestorNetID}@illinois.edu'
boxFolderName = f'tdx_{tdxTicket}'
#
def setup_browser():
    """Set up the Chrome browser instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--enable-javascript")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)
    return driver

def canvasLogin(driver, canvasUser, canvasPass, canvasAuthURL):
    """Authenticate the user."""
    driver.get(canvasAuthURL)
    usernameField = driver.find_element(By.XPATH, '//*[@id="pseudonym_session_unique_id"]')
    passwordField = driver.find_element(By.XPATH, '//*[@id="pseudonym_session_password"]')
    submitButton = driver.find_element(By.XPATH, '/html/body/div[3]/div[2]/div/div/div[1]/div/div/div/div/div/div[2]/form[1]/div[3]/div[2]/input')

    usernameField.send_keys(canvasUser)
    passwordField.send_keys(canvasPass)
    submitButton.click()

    # Optionally, verify login success
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="global_nav_profile_link"]'))
    )
    print("  = Login successful")

def student_access_report_export(driver, reportURL, targetFilePath):
    """Scroll to load JavaScript content and export the page to a PDF."""
    driver.get(reportURL)
    try:
        # Scroll to the bottom of the page to load all content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="content"]'))
        )
        print("  = JavaScript content loaded successfully")
        #print()

        # Export the page to a PDF
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "format": "A4",  # Set the page format (e.g., A4, Letter)
            "printBackground": True  # Include background graphics
        })

        # Decode the base64-encoded PDF data
        decoded_pdf_data = base64.b64decode(pdf_data["data"])

        # Save the decoded PDF data to a file
        with open(targetFilePath, "wb") as pdf_file:
            pdf_file.write(decoded_pdf_data)
        print()
        print(f"  = Page exported to {targetFilePath} successfully")

    except TimeoutException:
        print("  !!! Error: Timeout while waiting for JavaScript content to load.")
        # Optionally, capture a screenshot for debugging
        driver.save_screenshot("timeout_error.png")
        print("  !!! Screenshot saved as 'timeout_error.png'.")

def uploadToBox(targetFilePath, targetFileName, boxParentFolderID, boxFolderName, requestorEmailAddress):
    try:
        # create target folder in BOX
        boxCreateTargetFolder = boxClient.folder(boxParentFolderID).create_subfolder(boxFolderName)
        boxTargetFolderID = int(boxCreateTargetFolder['id'])
        print('  = Successfully created the BOX target folder.')
        print()
        # upload local CSV file to new BOX target folder
        r = boxClient.folder(boxTargetFolderID).upload(targetFilePath, targetFileName)
        #print(r)
        print('  = Successfully uploaded the CSV to BOX.')
        # share new BOX target folder with TDX requestor
        x = boxClient.folder(boxTargetFolderID).collaborate_with_login(requestorEmailAddress,CollaborationRole.VIEWER)
        boxSharedLink = f'https://uofi.box.com/folder/{boxTargetFolderID}'
        print()
        print('  ==')
        print(f'  == Folder successfully shared in BOX:  {boxSharedLink}')
        print('  ==')
    except Exception as e:
        print(f'!!! Error During BOX Actions: {e}')

def main():
    """Main function to run the tests."""
    driver = setup_browser()
    try:
        print()
        canvasLogin(driver, canvasUser, canvasPass, canvasAuthURL)
        print()
        student_access_report_export(driver, reportURL, targetFilePath)
        print()
        uploadToBox(targetFilePath, targetFileName, boxParentFolderID, boxFolderName, requestorEmailAddress)
        print()
    finally:
        driver.quit()
        print(">>> Browser closed <<<.")
        print()

if __name__ == "__main__":
    main()
