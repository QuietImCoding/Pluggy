@echo off
pyinstaller -y -i pluggy.ico -w pluggy.py
copy pluggy.ico dist\pluggy
copy chromedriver.exe dist\pluggy
copy pluggy.png dist\pluggy
pause