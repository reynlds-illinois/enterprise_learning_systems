import pytest, time
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

@pytest.fixture()
def chrome_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--verbose")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)
    # Yield the WebDriver instance
    yield driver
    # Close the WebDriver instance
    driver.quit()

def test_canvasPageOpen(chrome_browser):
    """ Test the title of the Instructure Canvas website """
    chrome_browser.get("https://illinoisedu.beta.instructure.com/login/canvas")
    assert chrome_browser.title == "Canvas Login | Instructure"

def test_canvasFindUsername(chrome_browser):
    """ Test finding the username field and populating it """
    usernameField = chrome_browser.find_elements(By.XPATH, '//*[@id="pseudonym_session_unique_id"]')
    usernameField[0].click()
    usernameField[0].send_keys("<my_service_account>")

def test_canvasFindPassword(chrome_browser):
    """ Test finding the password field and populating it """
    passwordField = chrome_browser.find_elements(By.XPATH, '//*[@id="pseudonym_session_password"]')
    passwordField[0].click()
    passwordField[0].send_keys("<my_password>")

def test_canvasSubmit(chrome_browser):
    """ Test finding and activating the submit button """
    submitButton = chrome_browser.find_elements(By.XPATH, '/html/body/div[3]/div[2]/div/div/div[1]/div/div/div/div/div/div[2]/form[1]/div[3]/div[2]/input')
    submitButton[0].click()

def test_canvasLogout(chrome_browser):
    """ Test locating and activating the user account settings then logout """
    logoutButton = chrome_browser.find_elements(By.XPATH, '/html/body/div[4]/span/span/div/div/div/div/div/span/form/button')
    logoutButton[0].click()

def test_canvasFindExitUsername(chrome_browser):
    """ Test finding the username field and populating it """
    exitUsernameField = chrome_browser.find_elements(By.XPATH, '//*[@id="pseudonym_session_unique_id"]')
    usernameField[0].click()

def test_canvasPageClose(chrome_browser):
    """ Test closing the browser """
    chrome_browser.close()
