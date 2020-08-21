from typing import Set
import multiprocessing
import pandas as pd
from queue import Queue
from selenium import webdriver
from course_finder import full_search, get_driver, go_to_term, courses_to_csv
import re

def get_subjects(term: str) -> Set[str]:
    """
    Returns the set of valid subjects for the term term as 4-letter course codes.
    """
    driver = get_driver()
    driver = go_to_term(driver, term)
    subjects = list()
    for option in driver.find_elements_by_css_selector(r"#subj_id > option"):
        if not option.text == "All Subjects":
            subjects.append(re.search(string=option.text, pattern=r"\(([A-Z]{3,4})\)").groups()[0]) # Add the 4-letter course code to the list.
    driver.close()
    return subjects[0:5]

def add_to_results(term: str, subj: str, queue: Queue) -> None:
    """
    Adds all courses with subject subj to the DataFrame df.
    """
    results = full_search(term, subj, open_only=False)
    queue.put(results)
    print(f"Added subject {subj}")

def get_all_courses(term: str) -> pd.DataFrame:
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    pool = multiprocessing.Pool(processes=16)
    df = pd.DataFrame()
    subjects = get_subjects(term)
    args_list = zip((term,) * len(subjects), subjects, (queue,)*len(subjects))

    for res in pool.starmap(add_to_results, args_list):
        df = pd.concat([df, queue.get()])

    return df

if __name__ == "__main__":
    df = get_all_courses("Winter 2021")
    df.sort_values(by="CourseID", inplace=True)
    print(df)
    courses_to_csv(df, "multi_results.csv")
