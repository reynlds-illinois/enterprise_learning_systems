# perform Canvas use testing with headless browser and Python/Selenium
# use example:  pytest ./my_testing_script.py --json-report
#
#!/usr/bin/python
import os, sys, pytest, time
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
sys.path.append("/var/lib/canvas-mgmt/bin")
from canvasFunctions import *
env = getEnv()
canvasUser = env['cm.user']
canvasPass = env['cm.pass']
#
@pytest.fixture()
def chrome_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--verbose")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)
    yield driver
    driver.quit()
#
def test_canvasPageOpen(chrome_browser):
    """ Test the title of the Instructure Canvas website """
    chrome_browser.get("https://<MY_CANVAS_URL>/login/canvas")    # < URL here
    assert chrome_browser.title == "Canvas Login | Instructure"
#
def test_canvasFindUsername(chrome_browser):
    """ Test finding the username field and populating it """
    usernameField = chrome_browser.find_elements(By.XPATH, '//*[@id="pseudonym_session_unique_id"]')
    if len(usernameField) > 0:
        print('= Found username field')
        usernameField[0].click()
        print('= Clicked into username field')
        usernameField[0].send_keys("<MY_USERNAME>")               # < username here
        print('= Sent username to field')
#
def test_canvasFindPassword(chrome_browser):
    """ Test finding the password field and populating it """
    passwordField = chrome_browser.find_elements(By.XPATH, '//*[@id="pseudonym_session_password"]')
    if len(passwordField) > 0:
        print('= Found password field')
        passwordField[0].click()
        print('= Clicked into password field')
        passwordField[0].send_keys("<MY_PASSWORD")                # < password here
        print('= Sent password to field')
#
def test_canvasSubmit(chrome_browser):
    """ Test finding and activating the submit button """
    submitButton = chrome_browser.find_elements(By.XPATH, '/html/body/div[3]/div[2]/div/div/div[1]/div/div/div/div/div/div[2]/form[1]/div[3]/div[2]/input')
    if len(submitButton) > 0:
        print('= Found submit button')
        submitButton[0].click()
        print('= Clicked submit button')
#
def test_canvasLogout(chrome_browser):
    """ Test locating and activating the user account settings then logout """
    account = chrome_browser.find_elements(By.XPATH, '//*[@id="global_nav_profile_link"]')
    if len(account) > 0:
        account[0].click()
    logoutButton = chrome_browser.find_elements(By.XPATH, '/html/body/div[4]/span/span/div/div/div/div/div/span/form/button')
    if len(logoutButton) > 0:
        logoutButton[0].click()
#
def test_canvasFindExitUsername(chrome_browser):
    """ Test finding the username field and populating it """
    exitUsernameField = chrome_browser.find_elements(By.XPATH, '//*[@id="pseudonym_session_unique_id"]')
    if len(exitUsernameField) > 0:
        print('= Found exit username field')
        usernameField[0].click()
        print('= Clicked into exitusername field')
#
def test_canvasPageClose(chrome_browser):
    """ Test closing the browser """
    chrome_browser.close()
