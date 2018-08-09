from tkinter import filedialog
from tkinter import *
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageTk
import re
import csv

top = Tk()
user_vars = {}
driver = None
csvdat = []
resultdat = []
loadstatus = StringVar()
loadstatus.set("Not Yet Loaded")
available = StringVar()
selected = None
selector = None
paused = False
cliks = 0
logging = False


def asciify(s):
    return s.encode('ascii', errors='ignore').decode().strip()


def update_vars(dat):
    dat = [d for d in dat]
    fields = ", \n".join(dat) if len(dat) < 15 else ", \n".join(dat[:15]) + " ..."
    available.set("Available fields:\n" + fields)


def fix_file_ext(fname, ext):
    return fname if "." in fname else fname + ext


def all_indices(string, sub, offset=0):
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
    loadstatus.set("Loading CSV")
    global csvdat
    csvdat = []
    with open(fname, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        try:
            rfieldnames = [asciify(fieldname).replace(" ", "_") for fieldname in reader.fieldnames]
        except UnicodeDecodeError as e:
            messagebox.showerror("Parsing Error",
                                 "Unable to parse csv file due to unexpected unicode characters in column names. " +
                                 "Consider renaming your column names and trying agin. " +
                                 "If the problem persists, file an issue on Github")
            loadstatus.set("Import a CSV")
            available.set("")
            return
        update_vars(rfieldnames)
        for row in reader:
            row = {key.replace(" ", "_"): row[key] for key in row.keys()}
            csvdat.append(row)
    loadstatus.set("CSV loaded.")


def export_csv():
    fname = filedialog.asksaveasfilename(initialdir=".", title="Where should the file be saved?",
                                         filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
    if fname == "":
        return
    with open(fix_file_ext(fname, ".csv"), 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csvdat[0].keys())
        writer.writeheader()
        writer.writerows(csvdat)


def query_selector(css_selector, wait_time, friendly=False):
    try:
        return WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
    except exceptions.TimeoutException:
        if friendly:
            return None
        raise exceptions.InvalidSelectorException(css_selector)


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


def expand_boi(s):
    if '{' not in s:
        return s
    vars_needed = re.findall('{([^}]+)}', s)
    for var in vars_needed:
        s = s.replace('{' + var + '}', user_vars[var])
    return s


def parse_command(s, rownum):
    global driver
    tokens = s.split()
    if len(tokens) < 1 or driver is None:
        return
    try:
        if tokens[0] == 'click':
            global selected, selector
            selector = user_vars[tokens[1]]
            elem = query_selector(selector, 3)
            selected = elem
            driver.execute_script("document.querySelector('" + selector + "').click();")
            return
        if tokens[0] == "type":
            selected.send_keys(expand_boi(user_vars[tokens[1]]))
            return
        if tokens[0] == "put":
            totype = expand_boi(user_vars[tokens[1]]).replace("\n", "\\n").replace('"', '\\"')
            scriptyboi = 'document.querySelector("' + selector + '").value = "' + totype + '";'
            driver.execute_script(scriptyboi)
            return
        if tokens[0] == "clear":
            selected.send_keys(Keys.CONTROL + "a")
            selected.send_keys(Keys.DELETE)
            return
        if tokens[0] == "log":
            global logging
            if not logging:
                logging = True
            csvdat[rownum][tokens[1]] = user_vars[tokens[1]]
        if tokens[0] == "enter":
            selected.send_keys(Keys.RETURN)
            return
        if tokens[0] == 'goto':
            driver.get(user_vars[tokens[1]])
            return
        if tokens[0] == 'set':
            quotes = all_indices(s, "'")
            user_vars[tokens[1]] = s[quotes[0] + 1:quotes[1]]
            return
        if tokens[0] == 'get':
            elem = query_selector(user_vars[tokens[2]], 3, friendly=True)
            if elem is None:
                user_vars[tokens[1]] = ""
                return
            if elem.tag_name == 'input' or elem.tag_name == 'textarea':
                user_vars[tokens[1]] = elem.get_attribute("value")
            else:
                user_vars[tokens[1]] = elem.text
            return
        if tokens[0] == 'paste' and len(tokens) == 4:
            user_vars[tokens[1]] = user_vars[tokens[2]] + user_vars[tokens[3]]
            return
        if tokens[0] == 'cut':
            tokens = [len(user_vars[tokens[2]]) if t == 'END' else int(t) if t.isdigit() else t for t in tokens]
            if len(tokens) == 4:
                user_vars[tokens[1]] = user_vars[tokens[2]][:tokens[3]]
            elif len(tokens) == 5:
                user_vars[tokens[1]] = user_vars[tokens[2]][tokens[3]:tokens[4]]
            return
        if tokens[0] == 'confirm':
            ok = messagebox.askyesnocancel("Confirmation", "Does this look right?")
            if ok is None:
                raise TypeError("Abort mission")
            if not ok:
                raise LookupError()
            return
    except (exceptions.NoSuchWindowException, AttributeError) as e:
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
    for rownum in range(len(csvdat)):
        row = csvdat[rownum]
        try:
            user_vars = {k: row[k] if k in row.keys() else user_vars[k] for k in user_vars.keys() | row.keys()}
            for line in program:
                mainwindow.update()
                parse_command(line.strip(), rownum)
        except ValueError:
            messagebox.showwarning("Browser Session Disconnected", "Your browser session was disconnected")
            return
        except KeyError as e:
            messagebox.showerror("Program Error", "Variable "
                                 + str(e)
                                 + " not found. Check your spelling and capitalization." +
                                 " Remember any spaces in variable names are replaced with underscores")
            return
        except IndexError:
            messagebox.showerror("Program Error", "Syntax error. Make sure all commands have the right amount of args" +
                                 " and that you're only using single quotes.")
            break
        except exceptions.InvalidSelectorException as ise:
            messagebox.showerror("Program Error", "Unable to find selector '" +
                                 str(ise)[str(ise).find(':') + 2:].strip() +
                                 "'. Make sure you're using the right selectors and check your click commands.")
            return
        except LookupError:
            continue
        except TypeError:
            return
    if logging:
        export_csv()


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
            parse_command(line.strip(), 0)
        update_vars(user_vars.keys())
    except ValueError:
        messagebox.showwarning("Browser Session Disconnected", "Your browser session was disconnected")
    except KeyError as e:
        messagebox.showerror("Program Error", "Variable "
                             + str(e)
                             + " not found. Check your spelling and capitalization. "
                             + "Remember any spaces in variable names are replaced with underscores")
    except IndexError:
        messagebox.showerror("Program Error", "Syntax error. Make sure all commands have the right amount of args" +
                             " and that you're only using single quotes.")
        return
    except exceptions.InvalidSelectorException as ise:
        messagebox.showerror("Program Error", "Unable to find selector '" +
                             str(ise)[str(ise).find(':') + 2:].strip() +
                             "'. Make sure you're using the right selectors and check your click commands.")
        return
    except LookupError:
        return
    except TypeError:
        return


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
    with open(fix_file_ext(fname, ".plgy"), "w") as fopen:
        text2save = str(tb.get("1.0", END))
        fopen.write(text2save)


def end_program():
    raise TypeError("problem")


def trap(e):
    global cliks
    cliks += 1
    if cliks > 1:
        v = messagebox.askyesno("Proceed with caution", "Are you the developer?")
        if v:
            for i in range(20):
                messagebox.showerror("Big mistake", "You have activated my trap card")
        cliks = 0


top.title("Pluggy")
top.iconbitmap("pluggy.ico")

# Code to add widgets will go here...
textarea = Text(top, height=6, width=30)
scrollbar = Scrollbar(top, command=textarea.yview)
scrollbar.place(in_=textarea, relx=1.0, relheight=1.0, bordermode="outside")
textarea.grid(row=0, column=1, sticky=N + E + S + W, padx=30, pady=10)

rightbtns = Frame(top)
browserbuttons = Frame(rightbtns)
popbtn = Button(browserbuttons, text="Start Browser", command=pop_a_window)
testbtn = Button(browserbuttons, text="Test program", command=lambda: test_program(textarea, top))
runbtn = Button(browserbuttons, text="Run program", command=lambda: run_program(textarea, top))
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
plabel.bind("<Button-1>", trap)
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
