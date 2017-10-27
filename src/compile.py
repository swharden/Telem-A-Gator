import py_compile
import glob
import time

exceptions=['_ui2py.pyw','compile.py','ui.py','run.py','run.pyc']

fnames=glob.glob("*.py*")
for fname in fnames:
    if fname in exceptions: continue
    if ".pyc" in fname: continue
    print "compiling",fname,"..."
    py_compile.compile(fname)
print "\nSUCCESS!"
time.sleep(1)
