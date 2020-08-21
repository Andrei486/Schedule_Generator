import time
import re
import json
import datetime
from typing import *
import arrow
from arrow import Arrow
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utilities import resource_path, driver_path

START_PAGE = r"https://central.carleton.ca/prod/bwysched.p_select_term?wsea_code=EXT"


class CourseInfo(pd.Series):
    def __init__(self, courseID: str, courseType: str, day: int,
                 startTime: datetime.time, endTime: datetime.time, secondDay: int = None, alsoRegister: str = None):

        data = [courseID, courseType, day, secondDay, startTime, endTime, alsoRegister]
        index = ["CourseID", "Type", "Day", "Day2", "Start", "End", "AlsoRegister"]
        super().__init__(data=data, index=index)


def get_driver() -> webdriver:
    """
    Creates and returns a Selenium-controller headless browser session
    on Chrome. Only call this once.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=chrome_options, executable_path=driver_path())
    return driver

def go_to_term(driver: webdriver, termName: str) -> webdriver:
    """
    Examples of term names are Fall 2019, Winter 2020, Summer 2020.
    """
    
    driver.get(START_PAGE)
    submitButton = driver.find_element_by_css_selector(
        r"input[value='Proceed to Search']")
    found = False
    for option in driver.find_elements_by_css_selector(r"#term_code > option"):
        if termName.replace(" ", "").lower() in option.text.replace(" ", "").lower() and not found:
            option.click()
            found = True

    if not found:
        print("Invalid term name.")
        return

    submitButton.click()
    return driver


def execute_search(driver: webdriver, subject: str, number: str, open_only: bool=True) -> webdriver:
    """
    Subject can be either the full name (Mathematics) or the four letter id (MATH).
    Either way, the match must be exact, so ids are preferred.
    If no subject is specified, defaults to "All Subjects".
    If using a CRN, it is recommended not to use other filters.
    """
    # set subject filter
    subjFound = False
    allSubjFound = False
    for option in driver.find_elements_by_css_selector(r"#subj_id > option"):
        # Click on the "all subjects" option to disable it (it is enabled by default)
        if not allSubjFound and option.text == "All Subjects":
            option.click()
            allSubjFound = True
        # Click on the option corresponding to the chosen subject
        if subject in option.text and not subjFound:
            option.click()
            subjFound = True
    if not subjFound:
        print("Could not find the subject {0}.".format(subject))
        driver.close()
        return None
    
    # set course number filter
    numberBox = driver.find_element_by_css_selector(r"#number_id")
    numberBox.send_keys(number)

    if open_only:
        # only search for open courses
        driver.find_element_by_css_selector(r'#special_id > option[value="O"]').click()
        # disable the "search for all courses" option
        driver.find_element_by_css_selector(r'#special_id > option[value="N"]').click()

    # start the search
    driver.find_element_by_css_selector(
        r"input[type='submit'][value='Search']").click()

    # verify that the search worked
    if not is_valid_results(driver):
        driver.close()
        return None
    print("Search successful.")
    return driver


def is_valid_results(driver: webdriver) -> bool:
    """
    Returns True if and only if the current page of driver is a valid course
    results page (waits for it to load first).
    """
    pageBanner = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, r"div.banner > h1"))).text
    if "search for courses" in pageBanner.strip().lower():
        # Too many courses were found or something went wrong
        print("The search produced too many results; try refining it?")
        return False
    else:
        try:
            driver.find_element_by_css_selector(r"span.warningtext")
            # No courses were found: the filters were too restrictive
            print("The search did not produce any results.")
            return False
        except NoSuchElementException:
            return True


def get_course_info(driver: webdriver) -> pd.DataFrame:
    """
    Returns the DataFrame of CourseInfo objects corresponding to the current page's
    search results.
    """
    if driver is None:
        return pd.DataFrame()
    
    courseTable = driver.find_element_by_css_selector(
        r"td > div > table > tbody")  # This selector is vulnerable to changes in the page!
    courses = []
    prevColor = None
    tableHTML = BeautifulSoup(courseTable.get_attribute("outerHTML"), "html.parser")
    rows = tableHTML.find_all("tr")
    currentInfo = []
    for row in rows:
        if row["bgcolor"] == prevColor or prevColor is None:
            currentInfo.append(row)
        else:
            courses.append(get_course_from_rows(currentInfo))
            currentInfo = [row]
        prevColor = row["bgcolor"]
    courses.append(get_course_from_rows(currentInfo))
    print("{0} courses found".format(len(courses)))
    return pd.DataFrame(courses)


def get_course_from_rows(rows: list) -> CourseInfo:
    """
    """
    mainRow = rows[0].find_all("td")
    courseID = mainRow[3].get_text().strip() + " "
    idWithSection = courseID + mainRow[4].get_text().strip()
    courseType = mainRow[7].get_text()

    scheduleInfo = rows[1].select_one('td[colspan]').get_text() if len(rows) >= 2 else ""
    
    if scheduleInfo:
        times = re.search(string = scheduleInfo, pattern = r"([0-9]{2}:[0-9]{2})\s*-\s*([0-9]{2}:[0-9]{2})")
        if times:
            times = times.groups()
            startTime = times[0]
            endTime = times[1]
    # Parse as time objects
    # startTime = time.strptime(times[0], "%H:%M")
    # endTime = time.strptime(times[1], "%H:%M")
        else:
            startTime = None
            endTime = None

        weekdays = re.search(string = scheduleInfo, pattern = r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Mon|Tue|Wed|Thu|Fri|Sat|Sun)*")
        weekdays = weekdays.groups() if weekdays else []
        day = weekdays[0] if len(weekdays) >= 1 else None
        secondDay = weekdays[1] if len(weekdays) >= 2 else None
    
        alsoRegisterInfo = rows[2].select_one('td[colspan]').get_text()

        alsoRegister = set()
        if "Also Register in:" in alsoRegisterInfo:
            # Remove base course name and "also register in"
            alsoRegisterInfo = re.sub(string = alsoRegisterInfo, pattern = "Also Register in:", repl="").strip()
            alsoRegisterInfo = re.sub(string = alsoRegisterInfo, pattern = courseID, repl="").strip()
            # Match section names
            
            for match in re.finditer(string = alsoRegisterInfo, pattern = r"([A-Z][A-Z]*[0-9]*)"):
                alsoRegister.add(courseID + match.groups()[0])
    else:
        startTime = None
        endTime = None
        day = None
        secondDay = None
        alsoRegister = set()
    
    return CourseInfo(courseID=idWithSection, courseType=courseType, day=day, secondDay=secondDay,\
        startTime=startTime, endTime=endTime, alsoRegister=alsoRegister)

def full_search(term: str, subject: str = "", number: str = "", open_only: bool=True) -> pd.DataFrame:
    """
    Returns a DataFrame where the rows are all the CourseInfo objects for
    the courses returned by the search for the given subject and number.
    """
    try:
        driver = get_driver()
        driver = go_to_term(driver, term)
        driver = execute_search(driver, subject=subject, number=number)
        courses = get_course_info(driver)
        if driver is not None:
            driver.close()
        return courses
    except BaseException as e:
        # On a failure, exit the Chrome headless session before raising the error.
        if driver is not None:
            driver.close()
        raise e

def search_all(term: str, courses: Set[str]) -> pd.DataFrame:
    """
    Returns a DataFrame where the rows are all the CourseInfo objects for
    the courses returned by the search for the given courses, in format
    XXXX 0000 (without the section).
    """
    results = pd.DataFrame()
    for course in courses:
        subject, number = parse_code(course)
        print(subject, number)
        results = pd.concat([results, full_search(term, subject, number)])
    return results

def courses_to_csv(course_df: pd.DataFrame, filepath: str) -> None:
    """
    Saves the course_df DataFrame to CSV in such a way that its data can
    be reconstructed later. Overwrites the file at filepath if there is one.
    """
    copied = course_df.copy()
    copied = copied.set_index("CourseID")
    # Use lists to be able to reconstruct them with JSON later.
    copied["AlsoRegister"] = copied["AlsoRegister"].apply(lambda s: list(s))
    copied.to_csv(filepath)

def search_from_query(filename: str) -> pd.DataFrame:
    """
    Executes a search according to the JSON query file at path filename,
    returning the course results as a DataFrame.
    """
    with open(filename, "r") as f:
        query = json.load(f)
        f.close()
    to_search = set(query["courses"] + query["electives"])
    print(to_search)
    term = query["term"]
    return search_all(term, to_search)

def parse_code(course_code: str) -> Tuple[str, str]:
    """
    Parses a course code of the form XXXX 0000 into a course subject and number.
    """
    info = re.search(string=course_code, pattern=r"([A-Z]{3,4})[ ]{0,1}([0-9]{4})").groups()
    subj = info[0]
    num = info[1] if len(info) > 1 else ""
    return (subj, num)

if __name__ == "__main__":
    df = search_from_query("query.json")
    courses_to_csv(df, "results.csv")