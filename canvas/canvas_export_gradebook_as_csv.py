#!/usr/bin/python
#
import os, sys, time, base64, requests
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
download_dir = '/var/lib/canvas-mgmt/reports/'
yesNo = ['y', 'n']
#
print()
courseID = input ('  > Enter the Course ID : ')
canvasCourseID = findCanvasCourse(courseID)
print()
#
input('  > Press Enter to continue... ')
#print()

# Set up the report URL and file name
#reportURL = f'{canvasURL}/courses/{canvasCourseID}/users/{canvasUserID}/usage'
#targetFileName = f'tdx_{tdxTicket}_access_report.pdf'
#targetFilePath = f'{reportsPath}{targetFileName}'
#requestorEmailAddress = f'{requestorNetID}@illinois.edu'
#boxFolderName = f'tdx_{tdxTicket}'
#
def setup_browser(download_dir=None):
    """Set up the Chrome browser instance with download support in headless mode and set window size."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--enable-javascript")
    # Set a typical desktop window size for headless mode
    chrome_options.add_argument("--window-size=1920,1080")

    # Set up download directory and preferences
    prefs = {}
    if download_dir:
        prefs["download.default_directory"] = os.path.abspath(download_dir)
        prefs["download.prompt_for_download"] = False
        prefs["download.directory_upgrade"] = True
        prefs["safebrowsing.enabled"] = True
        chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)

    # Enable downloads in headless mode
    if download_dir:
        params = {
            "behavior": "allow",
            "downloadPath": os.path.abspath(download_dir)
        }
        driver.execute_cdp_cmd("Page.setDownloadBehavior", params)

    # Set window size explicitly (for some Chrome versions)
    driver.set_window_size(1920, 1080)

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

# New function to download Canvas grade center CSV
def download_canvas_grade_center_csv(driver, canvasCourseID, download_dir):
    """
    Download the Canvas grade center CSV for a given course.
    Navigates to the gradebook, clicks the menu, then the export link.
    Takes a screenshot if the menu element is not found (for debugging headless mode).
    """
    gradebook_url = f"{canvasURL}/courses/{canvasCourseID}/gradebook"
    try:
        driver.get(gradebook_url)
        print(f"  = Navigating to gradebook for course ID {canvasCourseID}")
        print()
    except Exception as e:
        print(f"  !!! Error navigating to gradebook: {e}")
        print()
        return
    try:
        # Wait for the menu button to be present
        menu_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="Menu__label___2"]'))
        )
        menu_button.click()
        print("  = Gradebook menu opened")
        print()
    except Exception as e:
        print(f"  !!! Error opening gradebook menu: {e}")
        # Take a screenshot for debugging
        screenshot_path = os.path.join(download_dir or '.', 'gradebook_menu_not_found.png')
        driver.save_screenshot(screenshot_path)
        print(f"  !!! Screenshot saved to {screenshot_path}")
        print()
        return
    try:
        # Wait for the export link to be clickable
        #export_link = WebDriverWait(driver, 10).until(
        #    EC.element_to_be_clickable((By.XPATH, '/html/body/span[2]/span/span/span[2]/div/span[2]/span/span/span'))
        #)
        export_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'export-all'))
        )
        export_link.click()
        print("  = Export link clicked")
        print()
    except Exception as e:
        print(f"  !!! Error clicking export link: {e}")
        # Take a screenshot for debugging
        screenshot_path = os.path.join(download_dir or '.', 'export_link_not_found.png')
        driver.save_screenshot(screenshot_path)
        print(f"  !!! Screenshot saved to {screenshot_path}")
        print()
        return
    # Wait for the CSV to download (simple wait, or poll for file in download_dir)
    time.sleep(30)  # Adjust as needed for download time
    print(f"  = Grade center CSV download attempted. Check {download_dir} for the file.")

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
    driver = setup_browser(download_dir)  # Pass download_dir here!
    try:
        print()
        canvasLogin(driver, canvasUser, canvasPass, canvasAuthURL)
        print()
        download_canvas_grade_center_csv(driver, canvasCourseID, download_dir)
        # To upload the CSV add logic here to find the downloaded file and call uploadToBox
    finally:
        driver.quit()
        print(">>> Browser closed <<<.")
        print()

if __name__ == "__main__":
    main()
