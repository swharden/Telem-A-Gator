from telem import *
import ui_main
import sys
import traceback

from PyQt4 import QtCore, QtGui

### WE ASSUME THAT THIS IS __MAIN__


def setMenuPage(pageNumber=0):
    """determine which menu page (invisible tab) is displayed.
    
    ### REGULAR PAGES ###
    Page 0 - splash screen    
    Page 1 - data selection (.txt folder, .npy folder, convert)    
    Page 2 - experimental design (limits, binsize, etc)
    Page 3 - output options (interactive plot, images, excel, etc.)

    ### PARTIALLY HIDDEN PAGES ###    
    continued...
    """
    
    makeSchemeFromFields(True)
                 
    titles=['Telem-A-Gator','krfb.png',
            'Data Path Configuration','preferences-system-network.png',
            'Experimental Design','applications-science.png',
            'Data Analysis','gnumeric.png',
            'About Telem-A-Gator','user-info.png',
            'License Modification','txt.png',
            'Export Format','deluge.png',
            'Debug Log','geany.png',
            ]
    
    TG.debug("setting menu page %d"%pageNumber,4)
    uimain.stack.setCurrentIndex(pageNumber)

    uimain.lblTitleIcon.setPixmap(QtGui.QPixmap("icons/"+titles[pageNumber*2+1]))
    uimain.lblTitle.setText("  "+titles[pageNumber*2])
    
    #TG.schemeShow()

def setPath(key):
    path=str(QtGui.QFileDialog.getExistingDirectory(None, "Select Directory"))
    if path=="": return
    TG.scheme[key]=path
    populateFromScheme()   

def changeSelection():
    animals,features=[],[]
    for item in list(uimain.listAnimals.selectedItems()): 
        animals.append(str(item.text()))
    for item in list(uimain.listFeatures.selectedItems()): 
        features.append(str(item.text()))
    TG.scheme["animals"]=",".join(animals)
    TG.scheme["features"]=",".join(features) 
    
    selectionStart,selectionEnd=TG.selectedTimes()
    if selectionStart:
        uimain.lblFirstData.setText(ep2st(selectionStart))
        uimain.lblLastData.setText(ep2st(selectionEnd))
    


def makeSchemeFromFields(dontRepopulate=False):
    """Run this when FIELDS are changed. Updates scheme and repopulates fields again."""

    if not "input" in TG.scheme.keys(): return #catch premature repopulations

    needRepopulating=False #SLOW
    TG.debug("making scheme from fields",5)
    #TG.schemeRecalculate()
    
    
    
    if not TG.scheme["input"] == str(uimain.lineInputFolder.text()):    
        TG.scheme["input"]=str(uimain.lineInputFolder.text())
        needRepopulating=True
    if not TG.scheme["location"] == str(uimain.lineLocation.text()):    
        TG.scheme["location"]=str(uimain.lineLocation.text())
        TG.animals,TG.features=TG.listAvailable() 
        needRepopulating=True
        
    if uimain.chkSweeps.checkState()==QtCore.Qt.Checked: TG.scheme["sweep"]=True
    else: TG.scheme["sweep"]=False
    
    TG.scheme["baseline"]=uimain.grpBaseline.isChecked()
    
    if uimain.cmbVariance.currentIndex()==0: TG.scheme["stdev"]=False
    else: TG.scheme["stdev"]=True
        
    TG.scheme["expA"]=str(uimain.lineExpStartDate.text()+" "+uimain.lineExpStartTime.text())
    TG.scheme["expB"]=str(uimain.lineExpEndDate.text()+" "+uimain.lineExpEndTime.text())
    TG.scheme["expT"]=str(uimain.lineExpTitle.text())
    
    TG.scheme["baseA"]=str(uimain.lineBaseStartDate.text()+" "+uimain.lineBaseStartTime.text())
    TG.scheme["baseB"]=str(uimain.lineBaseEndDate.text()+" "+uimain.lineBaseEndTime.text())
    TG.scheme["baseT"]=str(uimain.lineBaseTitle.text())    
    

    TG.scheme["binnum"]=uimain.lineBinsize.text()
    TG.scheme["binunit"]=uimain.cmbBinsize.currentIndex()

    TG.scheme["plotKey"]=uimain.cmbFeature.currentIndex()
    TG.scheme["plotPrimary"]=uimain.chkPrimary.isChecked()
    TG.scheme["plotSecondary"]=uimain.chkSecondary.isChecked()
    TG.scheme["plotErrorBars"]=uimain.chkErr.isChecked()
    
    TG.scheme["plotBaseline"]=uimain.chkPlotBaseline.isChecked()
    TG.scheme["plotExperiment"]=uimain.chkPlotExperiment.isChecked()
    TG.scheme["plotNormalized"]=uimain.chkPlotNormalized.isChecked()
    
    #uimain.chkPlotBaseline.setEnabled(uimain.grpBaseline.isChecked())
    #TG.scheme["baseline"]=uimain.grpBaseline.isChecked()
        
    #TG.schemeShow()    
    TG.schemeRecalculate()
    updateRanges()
    if dontRepopulate==True: return
    populateFromScheme()

def btnSetTime1():
    uimain.lineExpStartDate.setText(str(uimain.lblFirstData.text()).split(" ")[0])
    uimain.lineExpStartTime.setText(str(uimain.lblFirstData.text()).split(" ")[1])
    makeSchemeFromFields()

def btnSetTime2():
    uimain.lineExpEndDate.setText(str(uimain.lblLastData.text()).split(" ")[0])
    uimain.lineExpEndTime.setText(str(uimain.lblLastData.text()).split(" ")[1])
    makeSchemeFromFields()

def btnSetTime3():
    uimain.lineBaseStartDate.setText(str(uimain.lblFirstData.text()).split(" ")[0])
    uimain.lineBaseStartTime.setText(str(uimain.lblFirstData.text()).split(" ")[1])
    makeSchemeFromFields()

def btnSetTime4():
    uimain.lineBaseEndDate.setText(str(uimain.lblLastData.text()).split(" ")[0])
    uimain.lineBaseEndTime.setText(str(uimain.lblLastData.text()).split(" ")[1])
    makeSchemeFromFields()

def populateFromScheme(lookForAnimals=False):
    """Run this when the SCHEME is changed."""
        
    TG.debug("repopulating fields from scheme",5)
    TG.schemeRecalculate()
    
    # PAGE 0 - splash page with licensing information    
    
    # PAGE 1 - data path configuration

    if TG.scheme["sweep"]==True: uimain.chkSweeps.setCheckState(QtCore.Qt.Checked)
    else: uimain.chkSweeps.setCheckState(QtCore.Qt.Unchecked)

    updateRanges()
    
    if lookForAnimals==True or TG.scheme["location"] <> str(uimain.lineLocation.text()):
        TG.debug("updaing LOCATION and repopulating fields")
        #TG.scheme["input"]=str(uimain.lineInputFolder.text())
        uimain.lineLocation.setText(os.path.abspath(TG.scheme["location"]))
        TG.animals,TG.features=TG.listAvailable()    

        uimain.listAnimals.clear()
        uimain.listAnimals.addItems(TG.animals)
        
        uimain.listFeatures.clear()
        uimain.listFeatures.addItems(TG.features)  
        

    goodToConvert=True

    uimain.progConvertFeature.setValue(0)
    uimain.progConvertFeature.setMaximum(len(TG.features))
    uimain.progConvertAnimal.setValue(0)
    uimain.progConvertAnimal.setMaximum(len(TG.animals))
    
    uimain.lineInputFolder.setText(os.path.abspath(TG.scheme["input"]))
    
    if os.path.exists(TG.scheme["input"]):
        nfiles=len(glob.glob(TG.scheme["input"]+"/*.txt"))
        uimain.lblInputLine1.setText("contains %d .txt files"%nfiles)
        uimain.lblInputLine2.setText("most recent update: TODO")
    else:
        uimain.lblInputLine1.setText("path does not exist")
        uimain.lblInputLine2.setText("")        
        goodToConvert=False

    #uimain.lineLocation.setText(TG.scheme["location"])
    if os.path.exists(TG.scheme["location"]):
        nfiles=len(glob.glob(TG.scheme["location"]+"/*.npy"))
        uimain.lblOutputLine1.setText("contains %d .txt files"%nfiles)
        uimain.lblOutputLine2.setText("most recent update:")
        uimain.lblOutputLine3.setText("no unconverted data detected") #TO DO
    else:
        uimain.lblOutputLine1.setText("path does not exist")
        uimain.lblOutputLine2.setText("")     
        uimain.lblOutputLine3.setText("")  
        goodToConvert=False

    uimain.btnConvert.setEnabled(goodToConvert)
    
    # PAGE 2 - experimental design
    
    
    uimain.grpBaseline.setChecked(TG.scheme["baseline"])
    
    for i in range(len(TG.animals)):
        if uimain.listAnimals.item(i).text() in TG.scheme["animals"].split(","):
            uimain.listAnimals.setItemSelected(uimain.listAnimals.item(i),True)
    
    for i in range(len(TG.features)):
        if uimain.listFeatures.item(i).text() in TG.scheme["features"].split(","):
            uimain.listFeatures.setItemSelected(uimain.listFeatures.item(i),True)
                   

                   
    uimain.lineExpStartDate.setText(TG.scheme["expA"].split(" ")[0])
    uimain.lineExpStartTime.setText(TG.scheme["expA"].split(" ")[1])
    uimain.lineExpEndDate.setText(TG.scheme["expB"].split(" ")[0])
    uimain.lineExpEndTime.setText(TG.scheme["expB"].split(" ")[1])
    uimain.lineExpTitle.setText(TG.scheme["expT"])
       
    uimain.lineBaseStartDate.setText(TG.scheme["baseA"].split(" ")[0])
    uimain.lineBaseStartTime.setText(TG.scheme["baseA"].split(" ")[1])
    uimain.lineBaseEndDate.setText(TG.scheme["baseB"].split(" ")[0])
    uimain.lineBaseEndTime.setText(TG.scheme["baseB"].split(" ")[1])
    uimain.lineBaseTitle.setText(TG.scheme["baseT"])    
    
    uimain.lineBinsize.setText(str(TG.scheme["binnum"]))
    uimain.cmbBinsize.setCurrentIndex(TG.scheme["binunit"])
    
    #if TG.scheme["variance"]: uimain.chkVariance.setCheckState(QtCore.Qt.Checked)
    #else: uimain.chkVariance.setCheckState(QtCore.Qt.Unchecked)
    
    if TG.scheme["stdev"]: uimain.cmbVariance.setCurrentIndex(1)
    else: uimain.cmbVariance.setCurrentIndex(0)
    
    uimain.cmbFeature.clear()   
    uimain.cmbFeature.addItems(TG.data.keys())
    uimain.cmbFeature.setCurrentIndex(TG.scheme["plotKey"])
            
    
    # PAGE 3 - data analysis
    
    uimain.lineOutputFolder.setText(TG.scheme["output"])
        
    changeSelection() #to update time ranges     
    if len(TG.data.keys())==0:
        uimain.grpOutput.setEnabled(False)
        uimain.framePreview.setEnabled(False)
    else:
        uimain.grpOutput.setEnabled(True)
        uimain.framePreview.setEnabled(True)
        
        
    if TG.scheme["plotPrimary"]: uimain.chkPrimary.setCheckState(QtCore.Qt.Checked)
    else: uimain.chkPrimary.setCheckState(QtCore.Qt.Unchecked)
    
    if TG.scheme["plotSecondary"]: uimain.chkSecondary.setCheckState(QtCore.Qt.Checked)
    else: uimain.chkSecondary.setCheckState(QtCore.Qt.Unchecked)
    
    if TG.scheme["plotErrorBars"]: uimain.chkErr.setCheckState(QtCore.Qt.Checked)
    else: uimain.chkErr.setCheckState(QtCore.Qt.Unchecked)
    
    if TG.scheme["plotBaseline"]: uimain.chkPlotBaseline.setCheckState(QtCore.Qt.Checked)
    else: uimain.chkPlotBaseline.setCheckState(QtCore.Qt.Unchecked)

    if TG.scheme["plotExperiment"]: uimain.chkPlotExperiment.setCheckState(QtCore.Qt.Checked)
    else: uimain.chkPlotExperiment.setCheckState(QtCore.Qt.Unchecked)

    if TG.scheme["plotNormalized"]: uimain.chkPlotNormalized.setCheckState(QtCore.Qt.Checked)
    else: uimain.chkPlotNormalized.setCheckState(QtCore.Qt.Unchecked)
    
    updateRanges()
        
    
def analyze():
    #uimain.mplwidget.setVisible(False)
    makeSchemeFromFields(True)
    uimain.mplwidget.axes.clear() 
    uimain.mplwidget.figure.canvas.draw()
    tryIt("scheme execute")
    populateFromScheme()
    tryIt("update plot")

    
def updateInlinePlot():  
    makeSchemeFromFields(True)
    uimain.mplwidget.axes.clear()  
    TG.plotFigure(uimain.mplwidget.figure)
    uimain.mplwidget.figure.canvas.draw()   
    
def saveScheme():
    makeSchemeFromFields()
    path=str(QtGui.QFileDialog.getSaveFileName(None, "Save Scheme As...","scheme.ini","*.ini"))
    TG.schemeSave(path)

def loadScheme():
    path=str(QtGui.QFileDialog.getOpenFileName(None, "Load Scheme From...","scheme.ini","*.ini"))
    TG.schemeLoad(path)    
    populateFromScheme(True)


def properlyFormattedTime(st):
    try:
        ep=st2ep(st)
        return True
    except:
        TG.debug("time improperly formatted",5)
        return False

def updateRanges():
    """error-check user-entered line edits on the experiment page."""
    
    paletteBad=QtGui.QPalette()
    paletteBad.setColor(uimain.lineExpStartDate.backgroundRole(),QtGui.QColor('red'))
    #paletteGood=uimain.lineStart.palette()
    paletteGood=QtGui.QPalette()
    paletteGood.setColor(uimain.lineExpStartDate.backgroundRole(),QtGui.QColor('white'))
    
    #EXP START    
    if properlyFormattedTime(str(uimain.lineExpStartDate.text())+" "+str(uimain.lineExpStartTime.text())): 
        uimain.lineExpStartDate.setPalette(paletteGood)
        uimain.lineExpStartTime.setPalette(paletteGood)
    else:
        uimain.lineExpStartDate.setPalette(paletteBad)
        uimain.lineExpStartTime.setPalette(paletteBad)
    
    #EXP END
    if properlyFormattedTime(str(uimain.lineExpEndDate.text())+" "+str(uimain.lineExpEndTime.text())): 
        uimain.lineExpEndDate.setPalette(paletteGood)
        uimain.lineExpEndTime.setPalette(paletteGood)
    else:
        uimain.lineExpEndDate.setPalette(paletteBad)
        uimain.lineExpEndTime.setPalette(paletteBad)

    #BASE START
    if properlyFormattedTime(str(uimain.lineBaseStartDate.text())+" "+str(uimain.lineBaseStartTime.text())): 
        uimain.lineBaseStartDate.setPalette(paletteGood)
        uimain.lineBaseStartTime.setPalette(paletteGood)
    else:
        uimain.lineBaseStartDate.setPalette(paletteBad)
        uimain.lineBaseStartTime.setPalette(paletteBad)

    #BASE END  
    if properlyFormattedTime(str(uimain.lineBaseEndDate.text())+" "+str(uimain.lineBaseEndTime.text())): 
        uimain.lineBaseEndDate.setPalette(paletteGood)
        uimain.lineBaseEndTime.setPalette(paletteGood)
    else:
        uimain.lineBaseEndDate.setPalette(paletteBad)
        uimain.lineBaseEndTime.setPalette(paletteBad)

    if TG.scheme["sweep"]==True or uimain.chkSweeps.checkState()==QtCore.Qt.Checked: 
        uimain.chkSweeps.setCheckState(QtCore.Qt.Checked)
        TG.scheme["sweep"]=True
        uimain.lineExpEndTime.setText(uimain.lineExpStartTime.text())
        uimain.lineExpEndTime.setEnabled(False)
        uimain.lineBaseEndTime.setText(uimain.lineExpStartTime.text())
        uimain.lineBaseEndTime.setEnabled(False)
        uimain.lineBaseStartTime.setText(uimain.lineExpStartTime.text())
        uimain.lineBaseStartTime.setEnabled(False)

    else: 
        uimain.chkSweeps.setCheckState(QtCore.Qt.Unchecked)
        TG.scheme["sweep"]=False
        uimain.lineExpEndTime.setEnabled(True)
        if TG.scheme["baseline"]==True:
            uimain.lineBaseEndTime.setEnabled(True)
            uimain.lineBaseStartTime.setEnabled(True)
            
    allGood=True

    if uimain.cmbBinsize.currentIndex()==0: mult=1
    if uimain.cmbBinsize.currentIndex()==1: mult=60
    if uimain.cmbBinsize.currentIndex()==2: mult=60*60
    if uimain.cmbBinsize.currentIndex()==3: mult=60*60*24
    
    try:
        sec=float(uimain.lineBinsize.text())
        totalSeconds=sec*mult
        if uimain.cmbBinsize.currentIndex()==0 and sec%10>0:
            TG.debug("bad second input - must be multiple of 10 seconds")
            allGood=False
        if (60*60*24)%totalSeconds>0:
            TG.debug("bad binsize - not divisible by 24hr")
            allGood=False
    except:
        allGood=False
            
    if allGood:
        uimain.lineBinsize.setPalette(paletteGood)
    else:
        uimain.lineBinsize.setPalette(paletteBad)
            


    
def tryIt(command=""):  
    try:
        TG.debug("attempting command: "+command,3)
        if command=="scheme execute":
            TG.schemeExecute()
            #analyze()
        if command=="update plot":
            updateInlinePlot()
        if command=="export excel":
            TG.outputExcel()
        if command=="export images":
            TG.outputImages()
        if command=="export HTML":
            TG.outputHTML()
    except Exception:
        details=traceback.format_exc()
        TG.debug(command+" execution FAILED!\n\n\nDETAILS:\n"+details,1)
        return
    finally:
        TG.debug(command+" execution COMPLETE",3)
    
def summaryPopup():
    makeSchemeFromFields()
    TG.summaryPopup()

########################################################

### SET-UP PRIMARY CLASSES
TG = TelemSession()
app = QtGui.QApplication(sys.argv)

#QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
#QtGui.QApplication.setPalette(QtGui.QApplication.style().standardPalette())

### SET-UP WINDOWS

# WINDOW main
win_main = ui_main.QtGui.QMainWindow()
uimain = ui_main.Ui_win_main()
uimain.setupUi(win_main)


### PRE-POPULATE FIELDS OF INTEREST
uimain.cmbBinsize.addItems(['sec','min','hr'])
uimain.cmbVariance.addItems(['standard error','standard deviation'])
setMenuPage(0)

#TG.schemeCreateDefault()
TG.schemeLoad()
populateFromScheme()
uimain.mplwidget.axes.hold(True)







########################################
### ONLY CONNECTIONS BELOW THIS LINE ###
########################################

# menu buttons
uimain.btnMenuData.clicked.connect(lambda: setMenuPage(1))
uimain.btnMenuExperiment.clicked.connect(lambda: setMenuPage(2))
uimain.btnMenuOutput.clicked.connect(lambda: setMenuPage(3))

uimain.actionAbout.triggered.connect(lambda: setMenuPage(4))
uimain.actionUpdate_License.triggered.connect(lambda: setMenuPage(5))
uimain.actionExportFormat.triggered.connect(lambda: setMenuPage(6))

uimain.actionExit.triggered.connect(lambda: sys.exit(0))


# DROP DOWN MENU
# FILE
uimain.actionSave_Scheme.triggered.connect(saveScheme)
uimain.actionLoad_Scheme.triggered.connect(loadScheme)
# CONFIGURATION
uimain.actionDebug.triggered.connect(lambda: setMenuPage(7))
# ADVANCED
# HELP
uimain.actionLicensing.triggered.connect(lambda: setMenuPage(0))

f=open('changelog.html')
html=f.read()
f.close()
uimain.textBrowser.setText(html)

# scheme update events

# PAGE 1 - data
#uimain.lineInputFolder.textEdited.connect(makeSchemeFromFields)
#uimain.lineLocation.textEdited.connect(makeSchemeFromFields)
uimain.btnConvert.clicked.connect(TG.convert)

# PAGE 2 - experiment

uimain.listAnimals.currentItemChanged.connect(changeSelection)
uimain.listAnimals.clicked.connect(changeSelection)
uimain.listFeatures.currentItemChanged.connect(changeSelection)
uimain.listFeatures.clicked.connect(changeSelection)

uimain.btnSetRaw.clicked.connect(lambda: setPath("input"))
uimain.btnSetLocation.clicked.connect(lambda: setPath("location"))
uimain.btnSetOutputFolder.clicked.connect(lambda: setPath("output"))

uimain.actionSet_data_npy_path.triggered.connect(lambda: setPath("location"))
uimain.actionSet_raw_txt_path.triggered.connect(lambda: setPath("input"))
uimain.actionSet_output_folder.triggered.connect(lambda: setPath("output"))
uimain.actionBug.triggered.connect(TG.makeCrashLog)

uimain.btnSetTime1.clicked.connect(btnSetTime1)
uimain.btnSetTime2.clicked.connect(btnSetTime2)
uimain.btnSetTime3.clicked.connect(btnSetTime3)
uimain.btnSetTime4.clicked.connect(btnSetTime4)

uimain.chkSweeps.clicked.connect(makeSchemeFromFields)
uimain.lineBinsize.textEdited.connect(makeSchemeFromFields)
uimain.cmbBinsize.currentIndexChanged.connect(makeSchemeFromFields)
uimain.cmbVariance.currentIndexChanged.connect(makeSchemeFromFields)

uimain.lineExpStartDate.textChanged.connect(updateRanges)
uimain.lineExpStartTime.textChanged.connect(updateRanges)
uimain.lineExpEndDate.textChanged.connect(updateRanges)
uimain.lineExpEndTime.textChanged.connect(updateRanges)
uimain.lineBaseStartDate.textChanged.connect(updateRanges)
uimain.lineBaseStartTime.textChanged.connect(updateRanges)
uimain.lineBaseEndDate.textChanged.connect(updateRanges)
uimain.lineBaseEndTime.textChanged.connect(updateRanges)

uimain.btnSummary.clicked.connect(summaryPopup)

# PAGE 3 - ANALYZE

uimain.btnExecute.clicked.connect(analyze)
uimain.btnSaveScheme.clicked.connect(saveScheme)
uimain.mplwidget.figure.set_facecolor("#FFFFFF") 
uimain.cmbFeature.currentIndexChanged.connect(updateInlinePlot)
uimain.chkPrimary.clicked.connect(updateInlinePlot)
uimain.chkSecondary.clicked.connect(updateInlinePlot)
uimain.chkErr.clicked.connect(updateInlinePlot)

uimain.chkPlotBaseline.clicked.connect(updateInlinePlot)
uimain.chkPlotExperiment.clicked.connect(updateInlinePlot)
uimain.chkPlotNormalized.clicked.connect(updateInlinePlot)

uimain.btnLaunchInteractive.clicked.connect(TG.plotPopup) 

uimain.btnExcel.clicked.connect(lambda: tryIt("export excel"))
uimain.btnImages.clicked.connect(lambda: tryIt("export images"))
uimain.btnHTML.clicked.connect(lambda: tryIt("export HTML"))
uimain.btnOutputOpen.clicked.connect(lambda: launchPath(TG.scheme["output"]))


#######################
### DISPLAY WINDOWS ###
#######################
TG.uimain=uimain
TG.app=app
win_main.show()
sys.exit(app.exec_())