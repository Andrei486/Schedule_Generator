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

def contains_list(lst: List) -> List:
    """
    Returns True if and only if the list lst contains at least
    one element which is itself a list.
    """
    for element in lst:
        if isinstance(element, list):
            return True
    return False

def flatten(lst: List) -> List:
    """
    Flattens the list lst as much as possible, ie until at least one of its elements
    is not a list. Returns a copy.
    """
    if not isinstance(lst, list):
        # If lst is not a list, it is a single element, so it is flattened
        return [lst]
    elif contains_list(lst):
        # If lst contains more lists, flatten those
        flat = []
        for item in lst:
            flat.extend(flatten(item))
        return flat
    else:
        # If lst is a list but contains no others then it is flattened
        return lst

def remove_incomplete(schedules: Set[FrozenSet[str]]) -> Set[FrozenSet[str]]:
    """
    Removes all incomplete schedules from schedules, returning
    the remaining set of schedules.
    """
    return set(schedule for schedule in schedules if not schedule == "incomplete")

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