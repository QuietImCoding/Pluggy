from tkinter import filedialog
from tkinter import *
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.keys import  Keys
from selenium.common import exceptions
from PIL import Image, ImageTk
import csv, os

top = Tk()
user_vars = {}
driver = None
csvdat = []
resultdat = []
loadstatus = StringVar()
loadstatus.set("Not Yet Loaded")
available = StringVar()
selected = None
paused = False

def pause():
    print(paused)

def asciify(s):
    return s.encode('ascii', errors = 'ignore').decode()

def updateVars(dat):
    dat = [asciify(d) for d in dat]
    fields = ", \n".join(dat) if len(dat) < 15 else ", \n".join(dat[:15]) + " ..."
    available.set("Available fields:\n" + fields)


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
    csvdat = []
    with open(fname, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rfieldnames = [asciify(fieldname).replace(" ", "_") for fieldname in reader.fieldnames]
        updateVars(rfieldnames)
        for row in reader:
            row = {key.replace(" ", "_"): row[key] for key in row.keys()}
            csvdat.append(row)
    loadstatus.set(os.path.basename(fname) + " loaded.")


def export_csv():
    fname = filedialog.asksaveasfilename(initialdir=".", title="Where should the file be saved?",
                                         filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
    if fname == "":
        return
    with open(fname, encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile)
        writer.writerows(resultdat)

def pop_a_window():
    global driver
    if driver is None:
        driver = webdriver.Chrome()
        driver.get("https://web.tabliss.io/")
    else:
        openanyway = messagebox.askokcancel("Pluggy",
                                            "Only one webdriver can be used at a time. Are you sure you want to open another one?")
        if openanyway:
            driver = webdriver.Chrome()
            driver.get("https://web.tabliss.io/")


def parseCommand(s):
    global driver
    tokens = s.split()
    if len(tokens) < 2 or driver is None:
        return
    try:
        if tokens[0] == 'set':
            quotes = allindices(s, "'")
            user_vars[tokens[1]] = s[quotes[0] + 1:quotes[1]]
        if tokens[0] == 'paste' and len(tokens) == 4:
            user_vars[tokens[1]] = user_vars[tokens[2]] + user_vars[tokens[3]]
        if tokens[0] == 'click':
            global selected
            toclick = user_vars[tokens[1]]
            elem = driver.find_element_by_css_selector(toclick)
            selected = elem
            driver.execute_script("document.querySelector('" + toclick + "').click();")
        if tokens[0] == 'goto':
            driver.get(user_vars[tokens[1]])
        if tokens[0] == "type":
            selected.send_keys(user_vars[tokens[1]])
        if tokens[0] == "enter":
            selected.send_keys(Keys.RETURN)
    except (exceptions.NoSuchWindowException, exceptions.WebDriverException, AttributeError) as e:
        print(e)
        driver.quit()
        driver = None
        raise ValueError("Some webdriver related exception occurred.")


def run_program(tb, mainwindow):
    global driver
    if driver is None:
        messagebox.showerror("No open browser",
                             "Make sure you have a browser open before you run the script.")
        return
    program = tb.get("1.0", 'end-1c').split("\n")
    global user_vars
    user_vars = {}
    if len(csvdat) == 0:
        messagebox.showerror("No CSV loaded", "Be sure to load some data before you try to run your program.")
        return
    for row in csvdat:
        try:
            user_vars = {k: row[k] if k in row.keys() else user_vars[k] for k in user_vars.keys() | row.keys()}
            for line in program:
                mainwindow.update()
                parseCommand(line.strip())
        except ValueError:
            messagebox.showwarning("Browser Session Disconnected", "Your browser session was disconnected")
            break
        except KeyError as e:
            messagebox.showerror("Program Error", "Variable "
                                 + str(e)
                                 + " not found. Check your spelling and capitalization. Remember any spaces in variable names are replaced with underscores")
            break
        except IndexError:
            messagebox.showerror("Program Error", "Problem reading set command. Check your quotes.")
            break


def test_program(tb, mainwindow):
    global driver
    global csvdat

    if driver is None:
        messagebox.showerror("No open browser",
                             "Make sure you have a browser open before you run the script.")
        return
    program = tb.get("1.0", 'end-1c').split("\n")
    global user_vars
    user_vars = {}
    if len(csvdat) > 0:
        row = csvdat[0]
    else:
        messagebox.showerror("No CSV loaded", "Be sure to load some data before you try to run your program.")
        return
    try:
        user_vars = {k: row[k] if k in row.keys() else user_vars[k] for k in user_vars.keys() | row.keys()}
        for line in program:
            mainwindow.update()
            parseCommand(line.strip())
        updateVars(user_vars.keys())
    except ValueError:
        messagebox.showwarning("Browser Session Disconnected", "Your browser session was disconnected")
    except KeyError as e:
        messagebox.showerror("Program Error", "Variable "
                             + str(e)
                             + " not found. Check your spelling and capitalization. "
                             + "Remember any spaces in variable names are replaced with underscores")
    except IndexError:
        messagebox.showerror("Program Error", "Problem reading set command. Check your quotes.")


def open_program(tb):
    fname = filedialog.askopenfilename(initialdir="./scripts", title="Select file to Open",
                                       filetypes=(("Pluggy program", "*.plgy"), ("All files", "*.*")))
    if fname == "":
        return
    with open(fname, "r") as fopen:
        data = fopen.read()
        tb.delete("1.0", END)
        tb.insert("1.0", data)


def save_program(tb):
    fname = filedialog.asksaveasfilename(initialdir="./scripts", title="Where should the file be saved?",
                                         filetypes=(("Pluggy program", "*.plgy"), ("All files", "*.*")))
    if fname == "":
        return
    with open(fname if ".plgy" in fname else fname + ".plgy", "w") as fopen:
        text2save = str(tb.get("1.0", END))
        fopen.write(text2save)


def end_program():
    global driver
    if driver is not None:
        driver.quit()
        driver = None
    else:
        messagebox.showerror("No running program", "There is no program running that you can end.")

top.title("Pluggy")
top.iconbitmap("pluggy.ico")
# Code to add widgets will go here...
textarea = Text(top, height=6, width=30)
scrollbar = Scrollbar(top, command = textarea.yview)
scrollbar.place(in_= textarea, relx=1.0, relheight = 1.0, bordermode="outside")
textarea.grid(row=0, column=1, sticky=N + E + S + W, padx=30, pady=10)

rightbtns = Frame(top)
browserbuttons = Frame(rightbtns)
popbtn = Button(browserbuttons, text="Start Browser", command=pop_a_window)
testbtn = Button(browserbuttons, text="Test program", command=lambda: top.after(test_program(textarea, top)))
runbtn = Button(browserbuttons, text="Run program", command=lambda: top.after(run_program(textarea, top)))
quitbtn = Button(browserbuttons, text="End program", command=end_program)
popbtn.pack(side=LEFT, padx=5)
testbtn.pack(side=LEFT, padx=5)
runbtn.pack(side=LEFT, padx=5)
quitbtn.pack(side=LEFT, padx=5)

filebtns = Frame(rightbtns)
openbtn = Button(filebtns, text="Open program", command=lambda: open_program(textarea))
savebtn = Button(filebtns, text="Save program", command=lambda: save_program(textarea))
openbtn.pack(side=LEFT, padx=5)
savebtn.pack(side=LEFT, padx=5)

browserbuttons.pack(side=LEFT, padx=10)
filebtns.pack(side=LEFT, padx=10)
rightbtns.grid(row=1, column=1, sticky=S, padx=10, pady=10)

csvarea = Frame(top)
img = ImageTk.PhotoImage(Image.open("pluggy.png").convert("RGBA").resize((115, 125)))
plabel = Label(csvarea, image=img)
plabel.image = img
plabel.pack(padx=10, pady=10)
loadtitle = Label(csvarea, text="CSV status", font="TkDefaultFont 16 bold")
loadtitle.pack(fill="y", expand=True)
loadtitle.bind("<Button-1>", lambda e: print(top.geometry()))
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
top.minsize(800, 300)
top.mainloop()
if driver is not None:
    driver.quit()
