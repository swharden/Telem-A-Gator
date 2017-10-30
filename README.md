# Telem-A-Gator
The Telem-A-Gator is python-based GUI to view and analyze scientific telemetry data.

### Concepts
* The telemetry software outputs data in the form of massive text files (CSV format with .txt extension). Sample output is below.
* The raw text files are hundreds of megabytes in size. They are extremely slow to parse, especially over network drives. To speed up analysis time, an initial TXT->NPY conversion is performed. This produces hundreds of smaller NPY files which are already memory-mapped in a format Python can load rapidly. 
* NPY file format is like `266307-Pulse Pressure-1353942890-even.npy` 
  * Each NPY file corresponds to a single feature on a single day
  * Format code: `ORIGINAL-FEATURE-EPOCH-even.npy` where
    * `ORIGINAL` = the original filename
    * `FEATURE` = the type of data it contains (pulled from heater)
    * `EPOCH` = the date of the first line of data in the file ([epoch time](https://en.wikipedia.org/wiki/Epoch_(reference_date)))
    * `even` = ? I can't remember. Evenly spaced data maybe?

### Installation
_NOTE: It was a MASSIVE undertaking to get this software running again several years later. The basic reason is that WinPython does not ship with PyQt, and to use the old version no newer versions can be installed on the system. Traditionally this was done with PythonXY, but that software is no longer available online. I got it working with WinPython, but its different version of numpy required code changes. It works now (2017-10-30) on a Windows 10 machine so follow these instructions carefully. There is almost no flexibility for other versions of Python or supporting libraries._

* install [WinPython-64bit-2.7.12.4Zero](https://sourceforge.net/projects/winpython/files/WinPython_2.7/2.7.12.4/) locally
  * It helps to have full file access to the install path. I recommend installing it in Documents.
  * `C:\Users\swharden\Documents\important\WinPython-64bit-2.7.12.4Zero` (for me)
  * You do not have to set the user or system environment variables to add python.exe to the system path.
* install [PyQt4-4.11.4-gpl-Py2.7-Qt4.8.7-x64.exe](https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/) into the WinPython sub-folder containing python.exe
  * During the installation screen it asks to locate Python's installation folder. 
    * Give it the the full path to python.exe. This will be similar to the path above, but one folder deeper
    * `C:\Users\swharden\Documents\important\WinPython-64bit-2.7.12.4Zero\python-2.7.12.amd64` (for me)
* Install additional libraries
  * open `WinPython Command Prompt.exe` (in the WinPython folder)
  * `python -m pip install --upgrade pip` (to upgrade pip)
  * `pip install numpy` (to install [numpy](http://www.numpy.org))
  * `pip install matplotlib` (to install [matplotlib](http://matplotlib.org))
* Create a batch script to launch the telem-a-gator
  * It's just `"C:\path\to\python.exe" "C:\path\to\TELEM-A-GATOR.py"`
  * This can be made an icon on the desktop
  * Add `pause` to the end of the script to prevent it from closing if it crashes.
  * Check out my [launch script](src/LAUNCH.cmd)
  
### Example Use
_Run through this set of steps to demonstrate how this software runs_
* ***Data Conversion:*** Data has to be converted from TXT files to NPY files.
  * Go to the _data path configuration_ screen. Instructions are at the top.
  * I like to make my output folder the same as my input folder.
  * Click convert, and hundreds of smaller NPY files will be created.
* ***Experiment Design:***
  * If no animals show up, go back to the data conversion screen and set the data folder
  * Design your experiment here. TODO: document what all the boxes do.

### Miscellaneous
* **Licensing:** At one point long ago there was talk about providing Telem-A-Gator with CJFLab software (which Dr. Frazier wrote and distributes as pay-for software with a licensing system to protect it). I included licensing support inside Telem-A-Gator but it is not activated and can be effectively ignored for now. Licensing a collection of plain text python scripts is a weird concept to me. I think the plan was to have this program run as a combination of Python and C such that the licensing system would use that already available in C.
* **matplotlibwidget error** (if occurs) can be prevented by placing matplotlibwidget.py in to WinPython's ./lib/site-packages/ folder. Alternatively just make sure that file is in the same folder you are launching python from (i.e., the folder with the batch script).

### Telemetry File Format
* Example data is in [/data/](/data/)
* There is a small header, then data is traditional CSV.
* Files can be hundreds of megabytes in size

```
# File created 2013/05/13 14:18:59 Eastern Daylight Time (UTC -0400)
# Time: 2012/11/26 10:14:50
# UTC: 2012/11/26 15:14:50
# Period: Seconds
# Col: 267373.Pulse Pressure,267373,1,Pulse Pressure,mmHg
# Col: 267373.Systolic,267373,1,Systolic,mmHg
# Col: 267373.Pressure,267373,1,Pressure,mmHg
# Col: 267373.Heart Rate,267373,1,Heart Rate,BPM
# Col: 267373.Diastolic,267373,1,Diastolic,mmHg
# Col: 267373.Activity,267373,2,Activity,Counts/min
0,30.880,134.175,119.304,531.135,103.295,0.000
10,29.904,134.123,119.747,539.591,104.280,0.000
20,30.362,134.604,119.549,511.399,104.242,0.000
30,29.858,134.675,119.911,509.528,104.762,0.000
40,29.361,135.060,120.861,526.790,106.108,0.000
50,25.648,130.785,118.961,695.613,105.292,0.000
60,25.546,137.320,125.278,712.946,112.232,6.000
70,26.374,140.087,127.435,692.260,113.753,0.000
80,26.847,142.985,129.909,675.199,116.575,0.000
90,26.237,143.769,131.534,705.232,117.630,0.000
100,25.722,147.578,134.931,713.224,121.574,0.000
110,25.924,147.309,134.263,720.641,121.340,0.000
120,24.191,129.820,117.820,745.614,105.741,12.000
130,26.345,133.677,121.262,755.374,107.194,24.000
```
