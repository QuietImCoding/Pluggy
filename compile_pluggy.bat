@echo off

:build
del pluggy.zip
pyinstaller -y -i pluggy.ico -w pluggy.py
copy pluggy.ico dist\pluggy
copy chromedriver.exe dist\pluggy
copy pluggy.png dist\pluggy
move dist\pluggy .

:cleanup
del /s /f /q build
del /s /f /q dist
del /s /f /q __pycache__
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q __pycache__
del pluggy.spec