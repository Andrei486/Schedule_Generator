from schedule_generator import schedule
from utilities import to_dataframe
import tkinter as tk
import tkinter.filedialog
import subprocess

def SelectFile(entry: tk.Entry, title: str, extension: str) -> None:

    window = tk.Toplevel()
    window.withdraw()

    path = tkinter.filedialog.askopenfilename(title=title, filetypes=(("{0} files".format(extension),"*.{0}".format(extension)),("all files","*.*")))

    window.destroy()
    entry.delete(0, tk.END)
    entry.insert(0, path)
    return


def ShowSchedulingOptions() -> None:
    master = tk.Toplevel()
    master.title("Scheduling Options")

    
    def Activate() -> None:
        courses = course_file.get()
        query = query_file.get()
        output = output_file.get()
        if not courses or not query:
            text.config(fg="red", text="Missing one or more required files.")
            return
        else:
            text.config(fg="black", text="")
            schedules = schedule(course_file.get(), query_file.get())
            if output:
                to_dataframe(schedules).to_csv(output)
                subprocess.run(['start', output], check=True, shell=True)
            
    
    # Make UI for choosing the course list CSV
    tk.Label(master, 
            text="Available Courses", justify=tk.LEFT).grid(row=0, sticky=tk.W)

    course_file = tk.Entry(master)
    course_file.grid(row=0, column=1)
    tk.Button(master, text="Choose File", justify=tk.RIGHT, command=lambda: SelectFile(course_file, "Available Courses", "csv")).grid(row=0, column=2)

    # Make UI for choosing the query JSON file

    tk.Label(master, 
            text="Query File", justify=tk.LEFT).grid(row=1, sticky=tk.W)

    query_file = tk.Entry(master)
    query_file.grid(row=1, column=1)
    tk.Button(master, text="Choose File", justify=tk.RIGHT, command=lambda: SelectFile(query_file, "Scheduling Query File", "json")).grid(row=1, column=2)

    # Make UI for choosing an optional output file

    tk.Label(master, 
            text="Output File (Optional)", justify=tk.LEFT).grid(row=2, sticky=tk.W)

    output_file = tk.Entry(master)
    output_file.grid(row=2, column=1)
    tk.Button(master, text="Choose File", justify=tk.RIGHT, command=lambda: SelectFile(output_file, "Schedule Output File", "csv")).grid(row=2, column=2)

    # Create buttons for quit/activation
    tk.Button(master, 
            text='Schedule', 
            command=Activate).grid(row=3, 
                                        column=0,
                                        sticky=tk.W, 
                                        pady=4)
    text = tk.Label(master, text="")
    text.grid(row=3, column=1, columnspan=2)
    tk.Button(master, 
            text='Quit', 
            command=master.quit).grid(row=3, 
                                        column=3,
                                        sticky=tk.E, 
                                        pady=4)
    
    tk.mainloop()

root = tk.Tk()
root.withdraw()
ShowSchedulingOptions()