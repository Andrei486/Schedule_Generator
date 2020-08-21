import time
import re
import json
import datetime
from itertools import combinations
from typing import *
import arrow
from arrow import Arrow
import pandas as pd
import timeit
from utilities import *
from course_finder import CourseInfo

def preprocess(course_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns course_df after preprocessing it for analysis. course_df is expected to be in the
    format created by course_finder, saved to a CSV file.
    """
    course_df["Day"] = course_df["Day"].apply(lambda t: time.strptime(t, "%a").tm_wday)
    course_df["Day2"] = course_df["Day2"].apply(lambda t: None if pd.isna(t) else time.strptime(t, "%a").tm_wday)
    course_df["AlsoRegister"] = course_df["AlsoRegister"].apply(lambda s: set(json.loads(re.sub(string=s, pattern="'", repl='"'))))
    course_df = course_df.set_index("CourseID")
    return course_df

def get_lecture_set(course_df: pd.DataFrame, course_id: str) -> Set[str]:
    """
    Returns the set of all lecture section names in course_df in the course course_id.
    Course ID format is XXXX 0000 (e.g., ELEC 2501).
    """
    lecture_sections = set()
    course_df.sort_index()
    for section_name in course_df.index:
        if course_id in section_name and course_df.loc[section_name]["Type"] not in {"Laboratory", "Tutorial"}:
            lecture_sections.add(section_name)
    return lecture_sections

def is_scheduled(course: CourseInfo) -> bool:
    """
    Returns True if and only if the course course, contained in course_df,
    has a scheduled time and day.
    """
    return course.Day is None or course.Day2 is None or course.Start is None or course.End is None
    

def is_conflict(course_df: pd.DataFrame, course1: str, course2: str) -> bool:
    """
    Returns True if and only if the two courses course1 and course2, both
    contained in course_df, have one or more time conflicts.
    """
    c1 = course_df.loc[course1]
    c2 = course_df.loc[course2]
    if not is_scheduled(c1) or not is_scheduled(c2):
        return False # Cannot have a conflict if one course does not have a scheduled time
    
    # Conflicts cannot occur if the two courses do not share a weekday at least
    days1 = {int(day) for day in {c1.Day, c1.Day2} if not pd.isna(day)}
    days2 = {int(day) for day in {c2.Day, c2.Day2} if not pd.isna(day)}

    if not days1.intersection(days2):
        return False
    else:
        # A conflict then occurs if and only if times overlap
        return ((c1.Start > c2.Start and c1.Start < c2.End)\
            or (c1.End > c2.Start and c1.End < c2.End)
            or (c2.End > c1.Start and c2.End < c1.End)
            or (c2.Start > c1.Start and c2.Start < c1.End)
            or (c1.Start == c2.Start or c1.End == c2.End))

def generate_conflicts_graph(course_df: pd.DataFrame) -> Dict[str, Set[str]]:
    """
    Returns the edge-set representation of the graph in which vertices represent
    course sections, and undirected edges connect vertices whose courses conflict.
    """
    graph = dict()
    for course in course_df.index:
        conflicts = set()
        for other in course_df.index:
            if other != course and is_conflict(course_df, course, other):
                conflicts.add(other)
        graph[course] = conflicts
    
    return graph

def get_allowed_courses(conflict_graph: Dict[str, Set[str]], already_selected: Set[str], prohibited: Set[str]) -> Set[str]:
    """
    Returns the set of courses in course_df that do not conflict with any course names in
    already_selected, according to the graph conflict_graph.
    """
    all_courses = set(conflict_graph.keys())
    prohibited = already_selected.copy().union(prohibited)
    for course in already_selected:
        prohibited = prohibited.union(conflict_graph[course])
    return all_courses.difference(prohibited)

def generate_schedules(course_df: pd.DataFrame, conflict_graph: Dict[str, Set[str]], already_selected: List[str],\
    requirements: List[Set[str]], prohibited: Set[str]) -> List:
    """
    Recursively generates all the schedules with given requirements.
    """
    # If nothing more is required, don't add any more courses
    if requirements == []:
        return frozenset(already_selected)
    # Otherwise, select one of the remaining requirements (doesn't matter which)
    # and try adding in all its courses (separately).
    schedules = []

    allowed = get_allowed_courses(conflict_graph, set(already_selected), prohibited)
    # Deal with shorter requirements first: may not matter? Needs performance testing.
    requirements.sort(key=len)
    # Consider courses from a given requirement (the first) that do not conflict with those chosen.
    req = set(requirements[0]).intersection(allowed)
    for addition in req:
        # Remove the newly fulfilled requirement from the list,
        new_requirements = requirements.copy()
        new_requirements.pop(0)
        # and add the "also register" section of the new course as a requirement if needed.
        also_register = course_df["AlsoRegister"][addition]
        add_requirement = True
        # Don't add it if it is empty or a duplicate of an existing one.
        if not also_register or also_register in new_requirements:
            add_requirement = False
        # Don't add it if it is already fulfilled by a selected course.
        for course in already_selected + [addition]:
            if course in also_register:
                add_requirement = False
                break
        
        if add_requirement:
            new_requirements.append(also_register)
        # Add the new course to the list of already selected ones.
        schedules.append(generate_schedules(course_df, conflict_graph, already_selected + [addition], new_requirements, prohibited))
    return schedules

def generate_with_electives(course_df: pd.DataFrame, conflict_graph: Dict[str, Set[str]],\
    requirements: List[Set[str]], elective_requirements: List[Set[str]],
    prohibited: Set[str], elective_count: int) -> Set[FrozenSet[str]]:
    """
    Recursively generates all valid schedules meeting the requirements, including a number elective_count of
    requirements in elective_requirements.
    """
    schedules = set()
    if elective_count > 0:
        for combination in combinations(elective_requirements, elective_count):
            combination = list(combination)
            new_schedules = generate_schedules(course_df, conflict_graph, [], requirements + combination, prohibited)
            flattened = set(flatten(new_schedules))
            print(len(flattened))
            schedules = schedules.union(flattened)
    else:
        new_schedules = generate_schedules(course_df, conflict_graph, [], requirements, prohibited)
        flattened = set(flatten(new_schedules))
        schedules = schedules.union(flattened)
    print(len(schedules))
    return schedules

def schedule(course_df_path: str, query_path: str) -> Set[FrozenSet[str]]:
    """

    """
    df = pd.read_csv(course_df_path)
    df = preprocess(df)
    conflicts = generate_conflicts_graph(df)
    print(df)
    with open(query_path, "r") as f:
        query = json.load(f)
        f.close()
    courses = query["courses"]
    electives = query["electives"]
    elective_count = query["electiveCount"]
    prohibited = set(query["prohibited"])
    requirements = [list(get_lecture_set(df, course)) for course in courses]
    elective_requirements = [list(get_lecture_set(df, elective)) for elective in electives]
    schedules = generate_with_electives(df, conflicts, requirements, elective_requirements, prohibited, elective_count)
    return schedules

def coverage_sample(schedules: Set[FrozenSet[str]], size: int) -> Set[FrozenSet[str]]:
    """
    Returns a sample of schedules from schedules of size size which has the
    maximum coverage possible; ie, contains as many different sections as possible.
    """
    
    selected = set()
    if size >= len(schedules):
        return schedules
    while len(selected) < size:
        # Find the current coverage.
        coverage = set()
        for s in selected:
            coverage = coverage.union(s)
        # Find the schedule which gives the best coverage when added.
        best_schedule = set()
        best_union = -1 # So a schedule will be added even if it adds no coverage.
        for s in schedules:
            # Don't add a schedule twice.
            if s not in selected:
                new_union = len(coverage.union(s))
                if new_union > best_union:
                    best_union = new_union
                    best_schedule = s
        selected.add(frozenset(best_schedule))
    return selected

if __name__ == "__main__":
    schedules = schedule("test/results.csv", "test/test_query.json")
    print(coverage_sample(schedules, 17))
    print()
    print(section_counts(schedules))