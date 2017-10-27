# Telem-A-Gator
python-based GUI to view/analyze scientific telemetry data

### SETTING UP WITH PYTHON XY 
- Install "Python(x,y)-2.7.3.1.exe"
- it doesn't matter where it's installed. It will always create C:\Python27\

### SETTING UP WITH WINPYTHON 
- install WinPython-64bit-2.7.12.4Zero.exe somewhere (note where the python 2.7 folder lives)
- install PyQt4-4.11.4-gpl-Py2.7-Qt4.8.7-x64.exe (be sure to tell it where your python 2.7 lives)
- if you get a 'matplotlibwidget' error, copy matplotlibwidget.py to WinPython's ./lib/site-packages/
    -- alternatively, just make sure it lives in the same folder as telem.py

### RUNNING TELEM-A-GATOR 
- Edit LAUNCH.bat to reflect the absolute path to python.exe (python 2.7)
- Run it to start telemagator.
