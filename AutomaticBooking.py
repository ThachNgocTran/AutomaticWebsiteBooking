from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib3.exceptions import MaxRetryError
import datetime
import regex as re
from typing import List, Dict, Callable, Union
import winsound
import pathlib
import requests
from time import sleep
from argparse import ArgumentParser
from pathlib import Path
import sys
import psutil

def print_status(msg):
    print(f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}')

def get_chrome_driver():
    # Source: https://stackoverflow.com/a/48194907/1860314
    def _attach_to_session(executor_url, session_id):
        original_execute = WebDriver.execute
        def new_command_execute(self, command, params=None):
            if command == "newSession":
                # Mock the response
                return {'success': 0, 'value': None, 'sessionId': session_id}
            else:
                return original_execute(self, command, params)
        # Patch the function before creating the driver object
        WebDriver.execute = new_command_execute
        driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
        driver.session_id = session_id
        # Replace the patched function with original function
        WebDriver.execute = original_execute
        return driver

    def _create_new_session(current_session = None):
        if current_session:
            '''
            Although there is "driver.start_session()", which may help re-use the chromedriver.exe,
            I can't manage to do so. So to workaround, kill the left-over chromedriver.exe.
            '''
            for proc in psutil.process_iter():
                if proc.name() == "chromedriver.exe":
                    proc.kill()

        chrome_dir = pathlib.Path(r"./ChromeSelenium").absolute()
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={chrome_dir}")
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    last_session_file = Path("LastSession.txt")
    if last_session_file.is_file():
        # Attempt to recover.
        lines = last_session_file.read_text().split("\n")
        url_id = lines[0]
        session_id = lines[1]
        driver = _attach_to_session(url_id, session_id)
        try:
            title = driver.title
        except WebDriverException as wde:
            # chromedriver is there, but Chrome instance no longer exists.
            if "not reachable" in str(wde):
                driver = _create_new_session(driver)
            else:
                raise wde
        except MaxRetryError:
            # chromedriver is now dead.
            driver = _create_new_session()
    else:
        driver = _create_new_session()
    # Overwrite mode.
    last_session_file.write_text(f'{driver.command_executor._url}\n{driver.session_id}')
    return driver

def _getWebDriverWait(in_driver):
    wdw = WebDriverWait(in_driver, 5)
    def _predicate():
        return wdw
    return _predicate

def _wait_until_all_visible(css: str) -> List[WebElement]:
    # Wait for the elements to be visible.
    elements = getWebDriverWait().until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, css)))
    return elements

'''
For efficiency, assuming that the element is already visible!
'''
def _wait_until_clickable(css: WebElement):
    # Wait until clickable (visibility + enabled).
    getWebDriverWait().until(lambda in_driver: css if css.is_enabled() else None)
    return css

def _wait_until_enterable(css: WebElement):
    # Wait until clickable (visibility + enabled).
    getWebDriverWait().until(lambda in_driver: css if css.is_enabled() else None)
    return css

class StepData():
    def __init__(self, name: str, css_expected_title: str, css_actions: List[Dict[str, Union[str, Callable]]]):
        self.name = name
        self.css_expected_title = css_expected_title
        self.css_actions = css_actions

def execute_step(sd: StepData):
    css_expected_title = sd.css_expected_title
    css_actions = sd.css_actions
    # Wait for the title.
    try:
        _wait_until_all_visible(css_expected_title)
    except TimeoutException:
        raise Exception(f'TimeOut when looking for title [{css_expected_title}].')

    # Start doing actions:
    for idx, one_action in enumerate(css_actions):
        css_expected = one_action["css_expected"]
        try:
            elements = _wait_until_all_visible(css_expected)
        except TimeoutException:
            if "message_if_not_found" in one_action:
                raise Exception(f'{one_action["message_if_not_found"]}')
            else:
                raise Exception(f'TimeOut when looking for element(s) [{css_expected}] in action [{idx+1}].')

        if "action" in one_action:
            action = one_action["action"]
            element_to_act = elements[0]
            if "action_filter" in one_action:
                element_to_act = one_action["action_filter"](elements)

            if action == "click":
                _wait_until_clickable(element_to_act).click()
            elif action == "enter":
                enter_what = one_action["enter_what"]
                _wait_until_enterable(element_to_act).send_keys(enter_what)
                _wait_until_enterable(element_to_act).send_keys(Keys.ENTER)
            else:
                raise Exception("Unknown action.")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-url", dest="url", help="URL of booking site (for Website)", required=True)
    parser.add_argument("-url_openingtimes", dest="url_openingtimes", help="URL of opening times (for Restful API call)", required=True)

    args = parser.parse_args()
    url = args.url
    url_openingtimes = args.url_openingtimes

    # Köln Kerpen Testzentrum
    #url = "https://web.daslab.app/book/location/1051"
    #url_openingtimes = 'https://api.daslab.app/locations/1051/opening_times'

    # A more efficient way to check available slots.
    while True:
        response = requests.get(url_openingtimes)
        if response.status_code == requests.codes.ok:
            body = response.json()
            if len(body["slots"]) > 0:
                break
            else:
                print_status("No slot available.")
        else:
            print_status(f'Status not ok. [{response.status_code}]')
        sleep(5)

    print_status(f'Found a slot! Start registering right now!')
    winsound.PlaySound(r'C:\Windows\Media\Alarm01.wav', winsound.SND_FILENAME)

    driver = get_chrome_driver()
    getWebDriverWait = _getWebDriverWait(driver)

    def _choose_slot_having_most_remaining_capacity(eles: List[WebElement]) -> WebElement:
        best_ele = None
        best_slot_avai = -1
        for one_ele in eles:
            text_slot = one_ele.find_elements_by_css_selector("div.item-footer")[0].text
            if text_slot == "Available slots":
                best_ele = one_ele
                break
            else:
                slot_avai = int(re.search("^([0-9]+) slot", text_slot).group(1))
                if slot_avai > best_slot_avai:
                    best_slot_avai = slot_avai
                    best_ele = one_ele
        return best_ele

    try:
        driver.get(url)

        step1 = StepData("Choose Date and Slot",
                         "div[data-name='book-location'] > * > * > div.title",
                         [{
                             "css_expected": "input[type='text']",
                             "action": "click"
                         },
                         {
                             "css_expected": "div.calendar-month.calendar-month-current > * > div.calendar-day:not(.calendar-day-disabled)",
                             "action": "click"
                         },
                         {
                             "css_expected": "li.media-item > a.item-link",
                             "action_filter": _choose_slot_having_most_remaining_capacity,
                             "action": "click"
                         }])

        # First product => the 1st dose.
        step2 = StepData("Choose Product",
                         "div[data-name='book-product'] > * > * > div.title",
                         [{
                             "css_expected": "li.media-item > a.item-link",
                             "action": "click",
                             "action_filter": lambda in_eles: in_eles[0]
                         }])

        step3 = StepData("Choose Person Quantity",
                         "div[data-name='book-quantity'] > * > * > div.title",
                         [{
                             "css_expected": "li.media-item > a.item-link",
                             "action": "click",
                             "action_filter": lambda in_eles: in_eles[0]
                         }])

        step4 = StepData("Fill in Person Credentials",
                         "div[data-name='book-patient'] > * > * > div.title",
                         [{
                             "css_expected": "div.PatientsList > * > * > * > li.media-item[data-cy='existing-patient-item'] > a.item-link",
                             "action": "click",
                             "action_filter": lambda in_eles: in_eles[0]
                         }])

        step5 = StepData("Check Booking Summary & Confirm",
                         "div[data-name='book-summary'] > * > * > div.title",
                         [{
                             "css_expected": "div[data-cy='confirm-and-pay-button'] > a",
                             "action": "click"
                         },
                         {
                             "css_expected": "div.dialog.dialog-buttons-2 > div.dialog-buttons > span:nth-child(2)",
                             "action": "click"
                         }])

        step6 = StepData("Pay Fee",
                         "div[data-name='book-payment'] > * > * > div.title",
                         [{
                             "css_expected": "div.card > div > div > ul > li[data-cy='code-field']",
                             "message_if_not_found": "There is no code field, maybe it's asking to pay by card?"
                         },
                         {
                             "css_expected": "input[type='text']",
                             "action": "enter",
                             "enter_what": "KPM0815EB38"
                         },
                         {
                             "css_expected": "a[data-cy='pay-by-code-button']",
                             "action": "click"
                         }])

        steps = [step1, step2, step3, step4, step5, step6]

        for idx, step in enumerate(steps):
            print_status(f'Executing Step [{idx+1}]: {step.name}')
            execute_step(step)

        print_status("*** Done ***")
        driver.get_screenshot_as_file(f'DoneScreenShot_[{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}].png')
        winsound.PlaySound(r'C:\Windows\Media\Windows Print complete.wav', winsound.SND_FILENAME)
    except Exception as ex:
        print_status(ex)
        driver.get_screenshot_as_file(f'ErrorScreenShot_[{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}].png')
        winsound.PlaySound(r'C:\Windows\Media\Windows Error.wav', winsound.SND_FILENAME)
    finally:
        #driver.quit()
        pass
