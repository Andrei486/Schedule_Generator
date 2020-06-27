from typing import *
from schedule_generator import schedule, coverage_sample
from course_finder import search_from_query, courses_to_csv
from utilities import to_dataframe
import json
import tkinter as tk
import tkinter.filedialog
import tkinter.scrolledtext as tkst
import subprocess

def select_file(entry: tk.Entry, title: str, extension: str) -> None:

    window = tk.Toplevel()
    window.withdraw()

    path = tkinter.filedialog.askopenfilename(title=title, filetypes=(("{0} files".format(extension),"*.{0}".format(extension)),("all files","*.*")))

    window.destroy()
    entry.delete(0, tk.END)
    entry.insert(0, path)
    return

def select_folder(entry: tk.Entry, title: str) -> None:

    window = tk.Toplevel()
    window.withdraw()

    path = tkinter.filedialog.askdirectory(title=title)

    window.destroy()
    entry.delete(0, tk.END)
    entry.insert(0, path)
    return

def make_schedules() -> tk.Toplevel:
    master = tk.Toplevel()
    master.title("Scheduling Options")

    
    def activate() -> None:
        courses = course_file.get()
        query = query_file.get()
        output_dir = output_folder.get()
        output_full = output_dir + "/all_schedules.csv"
        output_sample = output_dir + "/sample_schedules.csv"
        sample_size = sample_selector.get()
        sample_size = int(sample_size) if sample_size else 5
        if not courses or not query or not output_dir:
            text.config(fg="red", text="Missing one or more required fields.")
            return
        else:
            text.config(fg="black", text="")
            all_schedules = schedule(course_file.get(), query_file.get())
            to_dataframe(all_schedules).to_csv(output_full)
            sample_schedules = coverage_sample(all_schedules, 5)
            to_dataframe(sample_schedules).to_csv(output_sample)
            if open_output.get():
                subprocess.run(['start', output_sample], check=True, shell=True)
            
    
    tk.Label(master, 
            text="""Select the query file and course data file (if you haven't generated these yet,
            do that first), as well as an output location for the full list of schedules.
            For the output folder, use an empty folder, as this may overwrite files.""").grid(row=0, columnspan=3)
    # Make UI for choosing the course list CSV
    tk.Label(master, 
            text="Available Courses", justify=tk.LEFT).grid(row=1, sticky=tk.W)

    course_file = tk.Entry(master)
    course_file.grid(row=1, column=1)
    tk.Button(master, text="Choose File (csv)", justify=tk.RIGHT,\
        command=lambda: select_file(course_file, "Available Courses", "csv")).grid(row=1, column=2)

    # Make UI for choosing the query JSON file

    tk.Label(master, 
            text="Query File", justify=tk.LEFT).grid(row=2, sticky=tk.W)

    query_file = tk.Entry(master)
    query_file.grid(row=2, column=1)
    tk.Button(master, text="Choose File (json)", justify=tk.RIGHT,\
        command=lambda: select_file(query_file, "Scheduling Query File", "json")).grid(row=2, column=2)

    # Make UI for choosing an optional output file

    tk.Label(master, 
            text="Output Folder", justify=tk.LEFT).grid(row=3, sticky=tk.W)

    output_folder = tk.Entry(master)
    output_folder.grid(row=3, column=1)
    tk.Button(master, text="Choose Folder", justify=tk.RIGHT,\
        command=lambda: select_folder(output_folder, "Schedule Output Folder")).grid(row=3, column=2)

    open_output = tk.IntVar()
    tk.Checkbutton(master, text="Open sample file after finishing?", variable=open_output).grid(row=4, column=0)
    tk.Label(master, text="Size of sample").grid(row=4, column=1)
    sample_selector = tk.Entry(master)
    sample_selector.grid(row=4, column=2)
    sample_selector.insert(0, "5")
    # Create buttons for quit/activation
    tk.Button(master, 
            text='Schedule', 
            command=activate).grid(row=5, 
                                        column=0,
                                        sticky=tk.W, 
                                        pady=4)
    text = tk.Label(master, text="")
    text.grid(row=5, column=1, columnspan=2)
    tk.Button(master, 
            text='Back', 
            command=master.quit).grid(row=5, 
                                        column=3,
                                        sticky=tk.E, 
                                        pady=4)
    
    master.protocol("WM_DELETE_WINDOW", master.quit)
    tk.mainloop()
    return master

class CourseSelector(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        new_course_frame = tk.Frame(self)
        tk.Label(new_course_frame, text="Course Subject (4 letters)").grid(row=0, column=0, padx=4, pady=4)
        course_subj = tk.Entry(new_course_frame)
        course_subj.grid(row=0, column=1, padx=4, pady=4)
        tk.Label(new_course_frame, text="Course Number (4 digits)").grid(row=0, column=2, padx=4, pady=4)
        course_number = tk.Entry(new_course_frame)
        course_number.grid(row=0, column=3, padx=4, pady=4)
        tk.Button(new_course_frame, text="Add Course",\
            command=lambda: self.add_course(course_subj.get(), course_number.get())).grid(row=1,\
                column=0, columnspan=2, padx=4, pady=4)
        tk.Button(new_course_frame, text="Remove Last Course",\
            command=lambda: self.remove_course()).grid(row=1,\
                column=2, columnspan=2, padx=4, pady=4)
        new_course_frame.pack(side=tk.TOP)

        course_list = tkst.ScrolledText(self, wrap=tk.WORD, width=10, height=10)
        course_list.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.course_list = course_list
    
    def add_course(self, subj: str, number: str) -> None:
        """
        Adds the course course to the list of courses in element.
        """
        if number and subj:
            existing_courses = self.get_courses()
            self.write_courses(existing_courses + [f"{subj} {number}"])
        return

    def remove_course(self) -> None:
        """
        Removes the last course from the list in element.
        """
        courses = self.get_courses()
        if len(courses) == 0:
            return
        courses = courses[:-1]
        self.write_courses(courses)
        return

    def write_courses(self, courses: List[str]) -> None:
        """
        Writes a list of courses to the text area.
        """
        self.course_list.delete(1.0, tk.END)
        self.course_list.insert(1.0, "\n".join(courses))
        return

    def get_courses(self) -> List[str]:
        """
        Returns the list of selected courses.
        """
        return [course for course in self.course_list.get(1.0, tk.END).splitlines() if course]

def make_query() -> tk.Toplevel:
    
    def activate() -> None:
        courses = course_selection.get_courses()
        electives = elective_selection.get_courses()
        term = term_selector.get()
        elective_count = elective_count_selector.get()
        elective_count = int(elective_count) if elective_count else 1
        output_file = query_file.get()

        if not courses or not term or not output_file:
            warning_text.config(fg="red", text="One or more required fields are empty.")
            return
        else:
            if elective_count > len(electives):
                warning_text.config(fg="red", text=f"Could only select {len(electives)} electives.")
                elective_count = len(electives)
            else:
                warning_text.config(fg="black", text="")
            
            query_object = {"courses": courses,\
                "electives": electives,
                "electiveCount": elective_count,
                "term": term}
            
            with open(output_file, "w") as f:
                json.dump(query_object, f)
                f.close()
            return
    
    master = tk.Toplevel()
    master.title("Create a Query")
    # Make UI for choosing a list of main courses
    tk.Label(master, 
            text="Add courses below, or add each course into the text area on a new line.", justify=tk.LEFT).pack(side=tk.TOP, fill=tk.X)

    course_selection = CourseSelector(master)
    course_selection.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Make UI for choosing a list of elective courses
    tk.Label(master, 
            text="Add electives below, or add each elective into the text area on a new line.", justify=tk.LEFT).pack(side=tk.TOP, fill=tk.X)

    elective_selection = CourseSelector(master)
    elective_selection.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    extra_options = tk.Frame(master)
    tk.Label(extra_options, text="Academic term (e.g., Fall 2020)").grid(row=0, column=0)
    term_selector = tk.Entry(extra_options)
    term_selector.grid(row=0, column=1, padx=4, pady=4)
    tk.Label(extra_options, text="How many electives should be chosen from the list?").grid(row=1, column=0)
    elective_count_selector = tk.Entry(extra_options)
    elective_count_selector.grid(row=1, column=1, padx=4, pady=4)
    elective_count_selector.insert(0, "1")
    tk.Label(extra_options, text="Output filepath for the query (will be overwritten)").grid(row=2, column=0)
    query_file = tk.Entry(extra_options)
    query_file.grid(row=2, column=1)
    tk.Button(extra_options, text="Choose File (json)", justify=tk.RIGHT,\
        command=lambda: select_file(query_file, "Scheduling Query File", "json")).grid(row=2, column=2)
    extra_options.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Make UI for choosing action buttons
    buttons = tk.Frame(master)
    warning_text = tk.Label(buttons, text="")
    warning_text.grid(row=0)
    tk.Button(buttons, 
            text='Create Query', 
            command=activate).grid(row=1, column=0)
    tk.Button(buttons, 
            text='Back', 
            command=master.quit).grid(row=1, column=2)
    buttons.pack(side=tk.BOTTOM)
    master.protocol("WM_DELETE_WINDOW", master.quit)
    tk.mainloop()
    return master

def do_search() -> tk.Toplevel:
    """

    """

    def activate() -> None:
        """
        Searches using the selected query and copies results to the selected output file.
        """
        query = query_file.get()
        output = output_file.get()
        if not query or not output:
            warning_text.config(fg="red", text="Missing one or more required fields.")
        else:
            warning_text.config(fg="black", text="")
            df = search_from_query(query)
            courses_to_csv(df, output)
        return

    master = tk.Toplevel()
    master.title("Search for Courses")

    tk.Label(master, text="Select the query file and output file location.").grid(row=0, columnspan=3)

    tk.Label(master, 
            text="Query File", justify=tk.LEFT).grid(row=1, column=0, sticky=tk.W)

    query_file = tk.Entry(master)
    query_file.grid(row=1, column=1)
    tk.Button(master, text="Choose File (json)", justify=tk.RIGHT,\
        command=lambda: select_file(query_file, "Search Query File", "json")).grid(row=1, column=2)
    
    tk.Label(master, 
            text="Output File", justify=tk.LEFT).grid(row=2, column=0, sticky=tk.W)

    output_file = tk.Entry(master)
    output_file.grid(row=2, column=1)
    tk.Button(master, text="Choose File (csv)", justify=tk.RIGHT,\
        command=lambda: select_file(output_file, "Results Output File", "csv")).grid(row=2, column=2)
    
    tk.Button(master, 
            text='Search', 
            command=activate).grid(row=3, column=0)
    
    warning_text = tk.Label(master, text="")
    warning_text.grid(row=3, column=1)

    tk.Button(master, 
            text='Back', 
            command=master.quit).grid(row=3, column=2)

    master.protocol("WM_DELETE_WINDOW", master.quit)
    tk.mainloop()
    return master

def main_window() -> None:
    """

    """
    master = tk.Toplevel()
    master.title("Select an Option")

    def separate_window(f) -> None:
        """
        Runs the function f, hiding this window until f completes
        and restoring it afterwards.
        """
        master.withdraw()
        other_window = f()
        other_window.destroy()
        master.deiconify()

    # For creating a query
    tk.Label(master, text=\
        """To create a query, add all the courses that should be registered in for the term,
        as well as a list of acceptable electives. This step is required to get course data
        and for scheduling.""").grid(row=0, column=0)
    tk.Button(master, text="Create Query File",\
        command = lambda: separate_window(make_query)).grid(row=0, column=1)

    tk.Label(master, text=\
        """After creating a query, get data from the official Carleton course page.
        This will create a file needed for scheduling, and may take some time (~30s at least)
        for multiple courses.""").grid(row=1, column=0)
    tk.Button(master, text="Get Course Data",\
        command = lambda: separate_window(do_search)).grid(row=1, column=1)

    tk.Label(master, text=\
        """Once query and course data files are created, generate schedules that will work for those
        courses. Also specify scheduling options.""").grid(row=2, column=0)
    tk.Button(master, text="Generate Schedules",\
        command = lambda: separate_window(make_schedules)).grid(row=2, column=1)
    
    tk.Button(master, 
            text='Quit', 
            command=master.quit).grid(row=3, column=0, columnspan=2)
    
    master.protocol("WM_DELETE_WINDOW", master.quit)
    tk.mainloop()
    

root = tk.Tk()
root.withdraw()
main_window()