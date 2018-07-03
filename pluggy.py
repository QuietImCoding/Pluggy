from tkinter import filedialog
from tkinter import *
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

top = Tk()

def loadCSVFile():
    fname = filedialog.askopenfilename(initialdir="/", title="Select file",
                                               filetypes=(("jpeg files", "*.jpg"), ("all files", "*.*")))


def popAWindow():
    driver = webdriver.Chrome()
    driver.get("http://www.python.org")
    assert "Python" in driver.title
    elem = driver.find_element_by_name("q")
    elem.clear()
    elem.send_keys("pycon")
    elem.send_keys(Keys.RETURN)

def parseCommand(s):
    tokens = s.split()
    if tokens[0] == 'click':



# Code to add widgets will go here...
w = Button ( top, text = "Import a CSV file", command = loadCSVFile )
w.pack()
top.mainloop()

