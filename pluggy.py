from tkinter import filedialog
from tkinter import *
from tkinter import messagebox
from selenium import webdriver
from selenium.common import exceptions
import csv, os

top = Tk()
user_vars = {}
driver = None
csvdat = []
loadstatus = StringVar()
loadstatus.set("Not Yet Loaded")
available = StringVar()
selected = None


def allindices(string, sub, offset=0):
    listindex = []
    i = string.find(sub, offset)
    while i >= 0:
        listindex.append(i)
        i = string.find(sub, i + 1)
    return listindex


def load_csv():
    fname = filedialog.askopenfilename(initialdir=".", title="Select csv file to load",
                                       filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
    if fname == "":
        return
    loadstatus.set("Loading " + os.path.basename(fname))
    global csvdat
    with open(fname) as csvfile:
        reader = csv.DictReader(csvfile)
        rfieldnames = [fieldname.replace(" ", "_") for fieldname in reader.fieldnames]
        fields = ", \n".join(rfieldnames) if len(rfieldnames) < 25 else ", \n".join(rfieldnames[:25]) + " ..."
        available.set("Available fields: " + fields)
        for row in reader:
            row = {key.replace(" ", "_"): row[key] for key in row.keys()}
            csvdat.append(row)
    loadstatus.set(os.path.basename(fname) + " loaded.")


def pop_a_window():
    global driver
    if driver is None:
        driver = webdriver.Chrome()
        driver.get("https://web.tabliss.io/")
    else:
        openanyway = messagebox.askokcancel("Pluggy", "Only one webdriver can be used at a time. Are you sure you want to open another one?")
        if openanyway:
            driver = webdriver.Chrome()
            driver.get("https://web.tabliss.io/")


def parseCommand(s):
    global driver
    tokens = s.split()
    if len(tokens) < 2:
        return
    try:
        if tokens[0] == 'set':
            global user_vars
            quotes = allindices(s, "'")
            user_vars[tokens[1]] = s[quotes[0] + 1:quotes[1]]
        if tokens[0] == 'paste' and len(tokens) == 4:
            user_vars[tokens[1]] = user_vars[tokens[2]] + user_vars[tokens[3]]
        if tokens[0] == 'click':
            global selected
            toclick = user_vars[tokens[1]]
            elem = driver.find_element_by_css_selector(toclick)
            selected = elem
            driver.execute_script("document.querySelector('" + toclick + "').click();" )
        if tokens[0] == 'goto':
            driver.get(user_vars[tokens[1]])
        if tokens[0] == "type":
            selected.send_keys(user_vars[tokens[1]])
    except exceptions.NoSuchWindowException:
        driver = None
        return

def run_program(tb, mainwindow):
    mainwindow.update()
    global driver
    if driver is None:
        messagebox.showerror("No browser opened!!",
                             "Open a browser and setup whatever you need before running this script")
    program = tb.get("1.0", 'end-1c').split("\n")
    global user_vars
    user_vars = {}
    try:
        for row in csvdat:
            user_vars = {k: row[k] if k in row.keys() else user_vars[k] for k in user_vars.keys() | row.keys()}
            for line in program:
                parseCommand(line.strip())
    except exceptions.NoSuchWindowException:
        driver = None
        return



def open_program(tb):
    fname = filedialog.askopenfilename(initialdir=".", title="Select file to Open",
                                       filetypes=(("Browser automation programs", "*.bap"), ("All files", "*.*")))
    if fname == "":
        return
    with open(fname, "r") as fopen:
        data = fopen.read()
        tb.delete("1.0", END)
        tb.insert("1.0", data)


def save_program(tb):
    fname = filedialog.asksaveasfilename(initialdir=".", title="Where should the file be saved?",
                                         filetypes=(("Browser automation programs", "*.bap"), ("All files", "*.*")))
    if fname == "":
        return
    with open(fname if ".bap" in fname else fname + ".bap", "w") as fopen:
        text2save = str(tb.get("1.0", END))
        fopen.write(text2save)


top.title("Pluggy")
top.iconbitmap("plug.ico")
# Code to add widgets will go here...
textarea = Text(top, height=6, width=30)
textarea.grid(row=0, column=1, sticky=N + E + S + W, padx=30, pady=10)

rightbtns = Frame(top)
browserbuttons = Frame(rightbtns)
runbtn = Button(browserbuttons, text="Run program", command=lambda: run_program(textarea, top))
popbtn = Button(browserbuttons, text="Start Browser", command=pop_a_window)
popbtn.pack(side=LEFT, padx=5)
runbtn.pack(side=LEFT, padx=5)

filebtns = Frame(rightbtns)
openbtn = Button(filebtns, text="Open program", command=lambda: open_program(textarea))
savebtn = Button(filebtns, text="Save program", command=lambda: save_program(textarea))
openbtn.pack(side=LEFT, padx=5)
savebtn.pack(side=LEFT, padx=5)

browserbuttons.pack(side=LEFT, padx=5)
filebtns.pack(side=LEFT, padx=5)
rightbtns.grid(row=1, column=1, sticky=S, padx=10, pady=10)

csvarea = Frame(top)
loadtitle = Label(csvarea, text="CSV status", font="TkDefaultFont 16 bold")
loadtitle.pack(fill="y", expand=True)
csvstatus = Label(csvarea, textvariable=loadstatus)
csvstatus.pack()
availfields = Label(csvarea, textvariable=available)
availfields.pack(fill="y", expand=True)

csvarea.grid(row=0, column=0, padx=10)
loadbtn = Button(top, text="Import a CSV", command=load_csv)
loadbtn.grid(row=1, column=0, sticky=S, padx=10, pady=10)

top.columnconfigure(0, weight=1)
top.columnconfigure(1, weight=1)
top.rowconfigure(0, weight=1)
top.mainloop()
