from typing import *
from collections import defaultdict
import pandas as pd

def length_histogram(schedules: Set[FrozenSet[str]]) -> DefaultDict[int, int]:
    """
    Returns a histogram of number of courses for each schedule in
    schedules.
    """
    histogram = defaultdict(int)
    for schedule in schedules:
        histogram[len(schedule)] += 1
    return histogram

def flatten_once(lst: List) -> List:
    """
    Flattens the list lst one level.
    """
    return [item for sublist in lst for item in sublist]

def can_flatten(lst: List) -> List:
    """
    Returns True if and only if the list lst contains only elements that
    are themselves lists.
    """
    for element in lst:
        if not isinstance(element, list):
            return False
    return True

def flatten(lst: List) -> List:
    """
    Flattens the list lst as much as possible, ie until at least one of its elements
    is not a list. Returns a copy.
    """
    copied = lst.copy()
    while can_flatten(copied):
        copied = flatten_once(copied)
    return copied

def to_dataframe(schedules: Set[FrozenSet[str]]) -> pd.DataFrame:
    """
    Converts the set of schedules into a pandas DataFrame for ease
    of representation.
    """
    max_courses = max(len(schedule) for schedule in schedules)
    columns = list(range(1, max_courses + 1))
    schedule_data = [to_series(schedule, max_courses) for schedule in schedules]
    df = pd.DataFrame(schedule_data)
    return df

def to_series(schedule: FrozenSet[str], max_courses: int) -> pd.Series:
    """
    Converts the schedule schedule into a pandas Series,
    with length max_courses.
    """
    index = list(range(1, max_courses+1))
    data = list(schedule)
    while len(data) < len(index):
        data.append(None)
    return pd.Series(data=data, index=index)