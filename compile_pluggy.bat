@echo off
:looks_cooler
color 0a

:build
del pluggy.zip
pyinstaller -y -F -i pluggy.ico -w pluggy.py
copy pluggy.ico dist
copy chromedriver.exe dist
copy pluggy.png dist
mkdir pluggy
move dist\* pluggy

:cleanup
del /s /f /q build
del /s /f /q dist
del /s /f /q __pycache__
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q __pycache__
del pluggy.spec

:zip_clean
C:\Users\Daniel.Monteagudo\Downloads\7-ZipPortable\App\7-Zip64\7z.exe a pluggy.zip pluggy
del /s /f /q pluggy
rmdir /s /q pluggy

:extract
del /s /f /q ..\..\pluggy
rmdir /s /q ..\..\pluggy
C:\Users\Daniel.Monteagudo\Downloads\7-ZipPortable\App\7-Zip64\7z.exe x pluggy.zip -o..\.. -y