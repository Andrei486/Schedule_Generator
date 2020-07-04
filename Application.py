from typing import *
import json
import os.path
import subprocess
import tkinter as tk
import tkinter.filedialog
from tkinter import ttk
from tkinter.font import *
import tkinter.scrolledtext as tkst
from schedule_generator import schedule, coverage_sample
from course_finder import search_from_query, courses_to_csv
from utilities import to_dataframe, resource_path

QUERY_PATH = "search_options.json"
RESULTS_PATH = "search_results.csv"
ALL_SCHEDULES_PATH = "all_schedules.csv"
SAMPLE_SCHEDULES_PATH = "sample_schedules.csv"

def select_file(entry: ttk.Entry, title: str, extension: str) -> None:

    window = tk.Toplevel()
    window.withdraw()

    path = tkinter.filedialog.askopenfilename(title=title, filetypes=(("{0} files".format(extension),"*.{0}".format(extension)),("all files","*.*")))

    window.destroy()
    entry.delete(0, tk.END)
    entry.insert(0, path)
    return

class ToggledFrame(tk.Frame):

    def __init__(self, parent, text="", style="Title", *args, **options):
        tk.Frame.__init__(self, parent, *args, **options)

        self.show = tk.IntVar()
        self.show.set(0)
        self.title_frame = ttk.Frame(self, style=f"{style}.TFrame")
        self.title_frame.pack(fill=tk.X, expand=True)

        ttk.Label(self.title_frame, text=text, style=f"{style}.TLabel").pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.toggle_button = ttk.Checkbutton(self.title_frame, width=2, text='+', command=self.toggle,
                                            variable=self.show, style=f"{style}.Toolbutton")
        self.toggle_button.pack(side=tk.LEFT)

        self.sub_frame = ttk.Frame(self)

    def toggle(self):
        if bool(self.show.get()):
            self.sub_frame.pack(fill=tk.X, expand=True)
            self.toggle_button.configure(text='-')
        else:
            self.sub_frame.forget()
            self.toggle_button.configure(text='+')

class CourseSelector(tk.Frame):
    def __init__(self, parent, style="Basic", *args, **options):
        tk.Frame.__init__(self, parent, *args, **options)
        new_course_frame = ttk.Frame(self, style=f"{style}.TFrame")
        ttk.Label(new_course_frame, text="Course Subject (4 letters)", style=f"{style}.TLabel").grid(row=0, column=0, padx=4, pady=4)
        course_subj = ttk.Entry(new_course_frame, style=f"{style}.TEntry")
        course_subj.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(new_course_frame, text="Course Number (4 digits)", style=f"{style}.TLabel").grid(row=0, column=2, padx=4, pady=4)
        course_number = ttk.Entry(new_course_frame, style=f"{style}.TEntry")
        course_number.grid(row=0, column=3, padx=4, pady=4)
        add_button = ttk.Button(new_course_frame, text="Add Course",\
            command=lambda: self.add_course(course_subj.get(), course_number.get()), style=f"{style}.TButton")
        add_button.grid(row=1,column=0, columnspan=2, padx=4, pady=4)
        remove_button = ttk.Button(new_course_frame, text="Remove Last Course",\
            command=lambda: self.remove_course(), style=f"{style}.TButton")
        remove_button.grid(row=1, column=2, columnspan=2, padx=4, pady=4)
        new_course_frame.pack(fill=tk.BOTH, expand=True)

        course_list = tkst.ScrolledText(self, wrap=tk.WORD, width=10, height=5)
        course_list.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.course_list = course_list
        self.new_course_frame = new_course_frame
        self.add_button = add_button
        self.remove_button = remove_button
        self.course_subj = course_subj
        self.course_number = course_number
    
    def add_course(self, subj: str, number: str) -> None:
        """
        Adds the course course to the list of courses in element.
        """
        if number and subj:
            existing_courses = self.get_courses()
            self.write_courses(existing_courses + [f"{subj[0:4]} {number[0:4]}"])
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

class SectionSelector(CourseSelector):
    def __init__(self, parent, style="Basic", *args, **options):
        CourseSelector.__init__(self, parent, *args, **options)
        ttk.Label(self.new_course_frame, text="Course Section", style=f"{style}.TLabel").grid(row=0, column=4, padx=4, pady=4)
        section_id = ttk.Entry(self.new_course_frame, style=f"{style}.TEntry")
        section_id.grid(row=0, column=5, padx=4, pady=4)
        self.add_button.destroy()
        self.add_button = ttk.Button(self.new_course_frame, text="Add Course", style=f"{style}.TButton",\
            command=lambda: self.add_course(self.course_subj.get(), self.course_number.get(), section_id.get()))
        self.add_button.grid(row=1, column=0, columnspan=3, padx=4, pady=4)
        self.remove_button.grid(row=1, column=3, columnspan=3, padx=4, pady=4)
        self.new_course_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def add_course(self, subj: str, number: str, section: str) -> None:
        """
        Adds the section course to the list of courses in element.
        """
        if number and subj:
            existing_courses = self.get_courses()
            self.write_courses(existing_courses + [f"{subj[0:4]} {number[0:4]} {section}"])
        return

class QueryCreator(tk.Frame):
    """
    Frame that includes widgets for selecting search options
    and executing the search.
    """
    def __init__(self, parent, style="Basic", *args, **options):
        tk.Frame.__init__(self, parent, *args, *options)

        def save_options() -> None:
            """
            Saves the selected search options and gets the
            corresponding course data.
            """
            courses = course_selection.get_courses()
            electives = elective_selection.get_courses()
            prohibited = prohibited_selection.get_courses()
            term = term_selector.get()
            elective_count = elective_count_selector.get()
            elective_count = int(elective_count) if elective_count else 1

            if not courses or not term:
                warning_text.config(fg="red", text="One or more required fields are empty.")
                return
            else:
                if elective_count > len(electives):
                    warning_text.config(fg="red", text=f"Could only select {len(electives)} electives.")
                    elective_count = len(electives)
                else:
                    warning_text.config(fg="black", text="The search has been saved.")
                
                query_object = {"courses": courses,\
                    "electives": electives,
                    "prohibited": prohibited,
                    "electiveCount": elective_count,
                    "term": term}
                
                with open(QUERY_PATH, "w") as f:
                    json.dump(query_object, f)
                    f.close()
                return
        
        def search() -> None:
            try:
                df = search_from_query(QUERY_PATH)
                courses_to_csv(df, RESULTS_PATH)
                warning_text.config(fg="black", text="Search successful.")
            except:
                warning_text.config(fg="red", text="Something went wrong with the search.")

        # Make frame for selecting general options
        extra_options = ttk.Frame(self, style=f"{style}.TFrame")
        ttk.Label(extra_options, style=f"{style}.TLabel", text="Select your search options, then press Save Options and Search.").grid(row=0, column=0, columnspan=2)
        ttk.Label(extra_options, text="Academic term (e.g., Fall 2020)", style=f"{style}.TLabel").grid(row=1, column=0)
        term_selector = ttk.Entry(extra_options, style=f"{style}.TEntry")
        term_selector.grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(extra_options, text="How many electives should be chosen from the list?", style=f"{style}.TLabel").grid(row=2, column=0)
        elective_count_selector = ttk.Entry(extra_options, style=f"{style}.TEntry")
        elective_count_selector.grid(row=2, column=1, padx=4, pady=4)
        elective_count_selector.insert(0, "1")
        extra_options.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Make UI for choosing action buttons
        buttons = ttk.Frame(self, style=f"{style}.TFrame",)
        warning_text = tk.Label(buttons, text="")
        warning_text.grid(row=0, column=1)
        ttk.Button(buttons, 
                text='Save Options', style=f"{style}.TButton",
                command=save_options).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(buttons, 
                text='Search', style=f"{style}.TButton",
                command=search).grid(row=0, column=2, sticky=tk.E)
        buttons.pack(fill=tk.X, expand=True)
        
        # Make collapsing widget for selecting required courses
        course_select = ToggledFrame(self, "Select Required Courses", "Subtitle")
        ttk.Label(course_select.sub_frame, style=f"{style}.TLabel",
            text="Add courses below, or add each course into the text area on a new line.").pack(side=tk.TOP, fill=tk.X)
        course_selection = CourseSelector(course_select.sub_frame, style=style)
        course_selection.pack(fill=tk.BOTH, expand=True)
        course_select.pack(fill=tk.X, expand=True)

        # Make collapsing widget for selecting electives
        elective_select = ToggledFrame(self, "Select Electives", "Subtitle")
        ttk.Label(elective_select.sub_frame, style=f"{style}.TLabel",
                text="Add electives below, or add each elective into the text area on a new line.").pack(side=tk.TOP, fill=tk.X)
        elective_selection = CourseSelector(elective_select.sub_frame, style=style)
        elective_selection.pack(fill=tk.BOTH, expand=True)
        elective_select.pack(fill=tk.X, expand=True)
        # Make UI for choosing a list of prohibited sections
        prohibited_select = ToggledFrame(self, "Select Prohibited Sections", "Subtitle")
        ttk.Label(prohibited_select.sub_frame, style=f"{style}.TLabel",
                text="Add prohibited sections below, or in the text area on a new line. Use sparingly.").pack(side=tk.TOP, fill=tk.X)
        prohibited_selection = SectionSelector(prohibited_select.sub_frame)
        prohibited_selection.pack(fill=tk.BOTH, expand=True)
        prohibited_select.pack(fill=tk.X, expand=True)


class ScheduleGenerator(tk.Frame):
    def __init__(self, parent, style="Basic", *args, **options):

        tk.Frame.__init__(self, parent, *args, **options)

        def activate() -> None:
            sample_size = sample_selector.get()
            sample_size = int(sample_size) if sample_size else 5

            all_schedules = schedule(RESULTS_PATH, QUERY_PATH)
            to_dataframe(all_schedules).to_csv(ALL_SCHEDULES_PATH)
            
            sample_schedules = coverage_sample(all_schedules, sample_size)
            print(len(sample_schedules))
            to_dataframe(sample_schedules).to_csv(SAMPLE_SCHEDULES_PATH)
            if open_output.get():
                subprocess.run(['start', SAMPLE_SCHEDULES_PATH], check=True, shell=True)
            

        ttk.Label(self, style=f"{style}.TLabel", text="""
        After saving your search options, select what schedules to generate and press Schedule.
        This will generate two files: one with all possible schedules, and another sample of schedules.
        The sample will include as many different sections as possible to avoid registration issues in case sections become full.
        """).grid(row=0, column=0, columnspan=3, sticky=tk.N+tk.S+tk.W+tk.E)
        open_output = tk.IntVar()
        ttk.Checkbutton(self, text="Open sample file after finishing?", variable=open_output, style=f"{style}.TCheckbutton").grid(row=1, column=0)
        ttk.Label(self, text="Size of sample", style=f"{style}.TLabel").grid(row=1, column=1)
        sample_selector = ttk.Entry(self, style=f"{style}.TEntry")
        sample_selector.grid(row=1, column=2)
        sample_selector.insert(0, "5")

        # Create buttons for quit/activation
        text = ttk.Label(self, text="")
        text.grid(row=4, column=0, columnspan=3, sticky=tk.N+tk.S+tk.W+tk.E)
        ttk.Button(self, 
                text='Schedule', style=f"{style}.TButton",
                command=activate).grid(row=5, 
                                            column=0,
                                            columnspan=3,
                                            sticky=tk.N+tk.S,
                                            pady=4)

class ScrollableFrame(ttk.Frame):
    """
    Credit goes to https://blog.tecladocode.com/tkinter-scrollable-frames/
    for this class.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: self.resize_window(e, canvas)
        )

        self.window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def resize_window(self, e, canvas) -> None:
        width = e.width
        canvas.itemconfig(self.window, width = width)
        print("resized")


def main_window() -> tk.Tk:
    """
    Creates, sets up and returns an instance of Tk to use as the main
    window. Only call once.
    """
    root = tk.Tk()
    root.title("Scheduling")
    root.geometry("1000x800+0+0")
    root.iconbitmap(resource_path('wingicon.ico'))
    root.protocol("WM_DELETE_WINDOW", root.quit)
    style = ttk.Style()
    titles = ("Georgia", 14)
    regular = ("Helvetica", 10)
    style.configure("Title.TFrame", foreground="white", background="SteelBlue4", relief="flat", font=titles)
    style.configure("Title.TLabel", foreground="white", background="SteelBlue4", relief="raised", font=titles)
    style.configure("Title.TCheckbutton", foreground="white", background="SteelBlue4", relief="raised", font=titles)
    style.configure("Title.Toolbutton", foreground="white", background="SteelBlue4", relief="raised", font=titles)
    style.configure("Subtitle.TFrame", foreground="white", background="SteelBlue2", relief="flat", font=titles)
    style.configure("Subtitle.TLabel", foreground="white", background="SteelBlue2", relief="raised", font=titles)
    style.configure("Subtitle.TCheckbutton", foreground="white", background="SteelBlue2", relief="raised", font=titles)
    style.configure("Subtitle.Toolbutton", foreground="white", background="SteelBlue2", relief="raised", font=titles)
    style.configure("Basic.TFrame", relief="flat", font=regular)
    style.configure("Basic.TEntry", relief="flat", font=regular)
    style.configure("Basic.TLabel", relief="flat", justify=tk.LEFT, font=regular)
    style.configure("Basic.TButton", relief="flat", justify=tk.RIGHT, font=regular)
    style.configure("Basic.TCheckbutton", relief="flat", justify=tk.RIGHT, font=regular)
    return root

if __name__ == "__main__":
    root = main_window()
    scroll_frame = ScrollableFrame(root)

    query_creator = ToggledFrame(scroll_frame.scrollable_frame, "Options Select", "Title")
    QueryCreator(query_creator.sub_frame, "Basic").pack(fill=tk.BOTH, expand=True)
    query_creator.pack(fill=tk.BOTH, expand=True)

    schedule_generator = ToggledFrame(scroll_frame.scrollable_frame, "Generate Schedules", "Title")
    ScheduleGenerator(schedule_generator.sub_frame, "Basic").pack(fill=tk.BOTH, expand=True)
    schedule_generator.pack(fill=tk.BOTH, expand=True)

    scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    root.protocol("WM_DELETE_WINDOW", root.quit)
    tk.mainloop()