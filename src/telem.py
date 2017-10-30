import time
import os
import glob
import datetime
import numpy
import threading
import subprocess
#import scipy.stats

from PyQt4 import QtCore, QtGui

import matplotlib
matplotlib.use('TkAgg')
matplotlib.rcParams['backend'] = 'TkAgg' 
import pylab

def shortenTo(s,maxsize=100):
    if len(s)<=maxsize: return s
    first=s[:maxsize/2]
    last=s[-maxsize/2:]
    return first+"..."+last
    

def messagebox(title,msg):
    #tempApp = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.information(QtGui.QDialog(),title,msg)
    #tempApp.exit(0)   
   
def com2lst(s):
    """separate CSVs to a list, returning [s] if no commas."""
    if "," in s: 
        s=s.split(",")
    else: 
        s=[s]
    return s

def ep2dt(ep): 
    """convert an epoch time to a datetime object."""
    return datetime.datetime.fromtimestamp(float(ep))

def ep2st(ep): 
    """convert epoch seconds to a string-formatted date."""
    return dt2st(ep2dt(ep))   

def ep2fn(ep): 
    """convert epoch seconds to a file-ready date."""
    dt=ep2dt(ep)   
    return dt.strftime('%Y-%m-%d-%H-%M-%S') 
    
def ep2xl(ep):
    dt=ep2dt(ep)
    
def dt2ep(dt): 
    """convert a datetime object to epoch seconds."""
    return time.mktime(dt.timetuple())
    
def dt2st(dt): 
    """convert a datetime object to string-formatted date."""
    return dt.strftime('%Y/%m/%d %H:%M:%S')
   
def st2dt(st): 
    """convert a string-formatted date to a datetime object."""
    st=str(st)
    return datetime.datetime.strptime(st,'%Y/%m/%d %H:%M:%S')

def st2ep(st): 
    """convert a string-formatted date to epoch seconds."""
    st=str(st)
    return dt2ep(st2dt(st))

def stripWhiteSpace(s):
    """eliminate spaces at ends of a string."""
    while s[0]==" ": s=s[1:]
    while s[-1]==" ": s=s[:-1]
    return s
         
threads=[]
def threadCmd(cmd):
    global threads
    threads.append(ThreadCMDs())
    threads[-1].cmd=cmd
    threads[-1].start()
    threads[-1].join()
    
def launchPath(path):
    cmd="explorer.exe "+os.path.abspath(path)
    threadCmd(cmd)

class ThreadCMDs(threading.Thread):
    def __init__(self):
        self.stdout = None
        self.stderr = None
        self.cmd = "cmd.exe"
        threading.Thread.__init__(self)

    def run(self):
        p = subprocess.Popen(self.cmd.split(),
                             shell=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        self.stdout, self.stderr = p.communicate()
   

class TelemSession:

    """Telemetry conversion and analysis session class.
    Load this once, and interact with it accordingly.
    """
    def __init__(self):
        self.schemeClear()
        self.dataClear()
        self.log=[]
        self.printLogLevel=15
        self.secPerLine=10
        self.processing=False 
        self.uimain=False
        self.app=False
        self.abortNow=False
        self.schemeLoad()
        #self.status="waiting"
        self.debug("loaded telemetry session class",4)
        
    ######################
    ### SCHEME OPTIONS ###
    ######################

    
    def scheme2txt(self,scheme,showIt=False):
        """Convert a scheme to text. Optionally print it to console."""
        keys=scheme.keys()
        keys.sort()
        out="# AUTOMATICALLY GENERATED SCHEME:\n"
        for key in keys: 
            val=scheme[key]
            if type(val)==str: 
                val='"'+val+'"'
                val=val.replace("\\","/")
            out+="%s: %s\n"%(key,val)
        return out

    def schemeLoad(self,fname="scheme_default.ini"):
        """load a scheme.ini file and populate the scheme."""
        self.debug("loading scheme from "+fname,3)
        if fname==None: fname="scheme_default.ini"
        if not os.path.exists(fname):
            self.debug("Default scheme not found!\nWill generate a new one.",5)
            self.schemeCreateDefault()
            self.schemeSave()            
            return
        f=open(fname)
        raw=f.readlines()
        f.close()
        for line in raw:
            if len(line)<3: continue
            line=line.replace("\n","")
            if line[0] in [" ","#","\n","\r"]: continue
            if not ":" in line: continue
            var,val=line.split(":",1)
            val=stripWhiteSpace(val)
            val=eval(val)
            self.scheme[var]=val
            self.debug("setting [%s] to [%s] (%s)"%(var,val,type(val)))
        self.listAvailable()
        self.schemeRecalculate()

    def schemeSave(self,fname="scheme_default.ini"):
        """save a scheme to a file."""
        self.debug("saving scheme to "+fname,3)
        out=self.scheme2txt(self.scheme)    
        self.debug("saving scheme:",fname)
        f=open(fname,'w')
        f.write(out)
        f.close()

    def schemeRecalculate(self):
        """go through and do math for auto-generated fields."""

        self.listAvailable()   
        
        try:
            
            if self.scheme["animals"]=="all": 
                self.scheme["animals"]=",".join(self.animals)
            if self.scheme["features"]=="all": 
                self.scheme["features"]=",".join(self.features)
            
            if self.scheme["binunit"]==0: self.scheme["binsize"]=int(float(self.scheme["binnum"]))
            if self.scheme["binunit"]==1: self.scheme["binsize"]=int(float(self.scheme["binnum"])*int(60))
            if self.scheme["binunit"]==2: self.scheme["binsize"]=int(float(self.scheme["binnum"])*int(60*60))
            if self.scheme["binunit"]==3: self.scheme["binsize"]=int(float(self.scheme["binnum"])*int(60*60*24))
    
            if self.scheme["sweep"]==True: #24 hour sweeps
                self.scheme["expSpanSec"]=60*60*24
                self.scheme["baseSpanSec"]=60*60*24
                self.scheme["basePoints"]=int(self.scheme["baseSpanSec"]/self.scheme["binsize"])
                self.scheme["expPoints"]=int(self.scheme["expSpanSec"]/self.scheme["binsize"])
            
            else:        
                self.scheme["expSpanSec"]=int(st2ep(self.scheme["expB"])-st2ep(self.scheme["expA"]))
                self.scheme["baseSpanSec"]=int(st2ep(self.scheme["baseB"])-st2ep(self.scheme["baseA"]))
                self.scheme["basePoints"]=int(self.scheme["baseSpanSec"]/self.scheme["binsize"])
                self.scheme["expPoints"]=int(self.scheme["expSpanSec"]/self.scheme["binsize"])
        except Exception:
            self.debug("could not recalculate!",5)            
            
    def schemeGood(self):
        """Returns True if the scheme is valid."""
        # TO DO
        return True
        
    def schemeShow(self):
        keys=self.scheme.keys()
        keys.sort()
        for key in keys:
            self.debug("%s = %s"%(key,self.scheme[key]),5)
        
    def schemeClear(self):
        """Completely clear scheme."""
        self.scheme={}
    
    def schemeCreateDefault(self):
        """Generate example/demo scheme."""
        self.scheme["location"]=os.path.abspath("./data-npy")
        self.scheme["input"]=os.path.abspath("./data-txt")
        self.scheme["output"]=r"./output"
        self.scheme["features"]="all"
        self.scheme["animals"]="all"

        self.scheme["baseA"]="2012/05/23 19:00:00"
        self.scheme["baseB"]="2012/06/08 19:00:00"
        self.scheme["baseT"]="baseline"        
        
        self.scheme["expA"]="2012/06/08 19:00:00"
        self.scheme["expB"]="2012/06/19 19:00:00"
        self.scheme["expT"]="experiment"
        
        self.scheme["baseline"]=True
        
        self.scheme["sweep"]=True
        self.scheme["binnum"]=1
        self.scheme["binunit"]=2 # 0=sec, 1=min, 2=hr, 3=day
        self.scheme["stdev"]=False
        
        
        ### FIGURE OPTIONS
        
        self.scheme["plotPrimary"]=True
        self.scheme["plotSecondary"]=False
        self.scheme["plotErrorBars"]=True
        self.scheme["plotKey"]=0

        self.scheme["plotExperiment"]=True
        self.scheme["plotBaseline"]=True
        self.scheme["plotNormalized"]=False

        ### THE FOLLOWING ARE AUTO-CALCULATED BY schemeRecalculate()
        #self.scheme["binsize"]=None #DO NOT SET THIS!
        #self.scheme["expSpanSec"]=None #DO NOT SET THIS!    
        
        
        self.schemeRecalculate()
            

    #######################
    ### DATA CONVERSION ###
    #######################
    

    def convert(self):
        """Given a folder of .txt data files, generate npy files."""
        folderIn=os.path.abspath(self.scheme["input"])
        folderOut=os.path.abspath(self.scheme["location"])
        files=glob.glob(folderIn+"/*.txt")

        for i in range(len(files)):
            if self.uimain and self.app: 
                self.uimain.progConvertAnimal.setMaximum(len(files))
                self.uimain.progConvertAnimal.setValue(i+1)
                self.uimain.lblConvertAnimal.setText(os.path.split(files[i])[1])
                self.app.processEvents()
            self.convertTxt2Npy(files[i],folderOut)
        
        
        self.uimain.progConvertAnimal.setValue(0)
        self.uimain.progConvertFeature.setValue(0)
        self.uimain.lblConvertAnimal.setText("complete")
        self.uimain.lblConvertFeature.setText("complete")
        messagebox("COMPLETE","file conversion complete!")
        
    
    def convertTxt2Npy(self,fnameIn,pathOut):
        """Takes an input .txt raw data file and outputs multiple .npy data files.
        
        ORIGINAL DATA FORMAT:
        For this to work, the export settings in the telemetry analysis software
        have to be configured as such:
                
            select all data, click export.
            File name: [I].txt (example: T12.txt)
            Time mode: elapsed time (seconds)
            Data format: width=3, precision=3
            checkbox enabled: Import compatible
            
        OUTPUT:
        Output format is numpy binary files (.npy) of evenly spaced data.
        Each point represents 10 seconds of time.
        Missing data are replaced by numpy.NaN
        
        """   
            
        filePathIn,fileNameIn=os.path.split(fnameIn)
        self.debug("LOADING: "+fnameIn)
        self.uimain.lblConvertFeature.setText("loading ...")
        self.app.processEvents()
        
        f=open(fnameIn)
        raw=f.read()
        f.close()
        raw=raw.split("\n")
    
        animals=[] #[T5,T5,T5]
        features=[] #[Activity,Diastolic,Heart Rate]
        data=[]
    
        self.debug("READING DATA")
        for i in range(len(raw)):
            line=raw[i]
            if len(line)<10: continue
            if line[0]=="#": # WE HAVE A HEADER LINE
                if "Time: " in line:
                    ep_start=st2ep(line.split(": ")[1])
                if "Col: " in line:
                    animal,feature=line.split(": ")[1].split(",")[0].split(".")
                    animals.append(animal)
                    features.append(feature)
            else: # WE HAVE A DATA LINE
                data.append(line.split(","))
            
        self.debug("CONVERTING TO MATRIX")
        self.uimain.lblConvertFeature.setText("converting to matrix ...")
        self.app.processEvents()
        
        data=numpy.array(data,dtype=float)
        self.debug("RESHAPING DATA")
        self.uimain.lblConvertFeature.setText("reshaping data ...")
        self.app.processEvents()
        
        data=numpy.reshape(data,(-1,len(animals)+1))
        data[:,0]=data[:,0]+ep_start #turn time stamps into epoch   
        
        if self.uimain and self.app: 
            self.uimain.progConvertFeature.setMaximum(len(features))
            self.app.processEvents()               
        
        for i in range(len(features)):
            
            if self.uimain and self.app: 
                self.uimain.progConvertFeature.setValue(i+1)
                #self.uimain.lblConvertFeature.setText(features[i])
                self.app.processEvents()               
            tag="%s-%s-%d"%(animals[i],features[i],ep_start)+"-even.npy"
            fname=os.path.join(pathOut,tag)
            self.debug("CONVERTING TO EVENLY SPACED DATA")
            self.uimain.lblConvertFeature.setText("spacing data ...")
            self.app.processEvents()
            
            timestamps=data[:,0].astype(int)
            values=data[:,i+1]
            indices=(timestamps-timestamps[0])/self.secPerLine        
            dayData=numpy.empty(indices[-1]+1,dtype=float)
            dayData[:]=numpy.nan
            dayData[indices]=values
            self.debug("SAVING "+tag)

            self.uimain.lblConvertFeature.setText("saving %s ..."%tag)
            self.app.processEvents()
        
            numpy.save(fname,dayData)
        return
    
    
    
    # to do

    ####################
    ### DATA LOADING ###
    ####################

    def listAvailable(self):
        """returns [animals,features] from scheme["location"]."""
        animals,features=[],[]
        self.animalInfo=[] #[animal,startEp,endEp]
        fnames=glob.glob(self.scheme["location"]+"/*-even.npy")
        for fname in fnames:
            fn,ft=os.path.split(fname)
            ft=ft.split("-")
            if not ft[0] in animals: 
                animals.append(ft[0])
                startEp=int(ft[2])
                length=numpy.memmap(fname).shape[0]
                info=[ft[0],startEp,startEp+length*self.secPerLine]
                #self.debug(str(info),5)
                self.animalInfo.append(info)
            if not ft[1] in features: features.append(ft[1])
        self.animals=animals
        self.features=features
        return [animals,features]
                       
    def selectedTimes(self):
        if len(self.animalInfo)==0: return [None,None]
        first=None
        last=None
        selAnimals=com2lst(self.scheme["animals"])
        for info in self.animalInfo:
            if info[0] in selAnimals:
                if first==None or info[1]<first: first=info[1]
                if last==None or info[2]>last: last=info[2]
        self.selectedExtremes=[first,last]
        return [first,last]
            
    def loadNpy(self,fname):
        """load a filename of a .npy and return [data,animal,feature,startEp,endEp].
        You probably don't need to call this directly. loadData() calls it."""    
        fpath,ftag=os.path.split(fname)
        #self.debug("\n\n",5)    
        self.debug("loading "+ftag,2)    
        data=numpy.load(fname) # pulls the whole thing to ram
        #data=numpy.memmap(fname) # MEMORY MAPPING IS FASTER IF BETTER DATA TYPE
        animal,feature,startEp,mode=ftag.split(".")[0].split("-")
        startEp=int(startEp)
        endEp=startEp+len(data)*self.secPerLine
        return [data,animal,feature,startEp,endEp]
    
    def loadData(self,animal=None,feature=None,location=None,startEpCut=False,endEpCut=False,binsize=False,sweep=False):
        """simple way to get data from animal/feature combo. return [x],[[ys]].
        if binsize is given (sec), binning will occur.
        If startEp and/or endEp are given (epoch), trimming will occur.
        
        if sweep == False:
            returns [X], [[Y]]
            where x = time epochs
            
        if sweep == True: (day starts at the time of startEpCut)
            returns [X], [[Y],[Y],[Y]]
            where x = ticks 0-24hr
            
            
        UPDATE: returns [xs,data,startX,startX+self.secPerLine2*len(data[0])]
        """
        
        ### DEMO DATA ###################################
        #startEpCut=st2ep("2012/06/01 19:00:00")    
        #endEpCut=st2ep("2012/06/10 19:00:00")    
        #binsize=60*60 #in seconds
        #sweep=True
        #################################################
              
        
        if location==None:
            location=self.scheme["location"]
        self.secPerLine2=self.secPerLine
        fnames=glob.glob(location+"/%s-%s*-even.npy"%(animal,feature))
        if len(fnames)==0:
            self.debug("%s - %s does not exist!"%(animal,feature),2)
            return []
        fname=fnames[0]
        data,animal,feature,startEp,endEp=self.loadNpy(fname)
        
        self.debug("data shape before cutting/padding: %s"%str(data.shape))
        
        if startEpCut==False: startEpCut=startEp       
        if endEpCut==False: endEpCut=endEp       
        
        expectedPoints=int((endEpCut-startEpCut)/self.secPerLine)
        offsetStart=int(startEpCut-startEp)/self.secPerLine

        if startEpCut:
            if offsetStart<0:
                # left padding is necessary
                padding=numpy.empty(abs(offsetStart))
                padding[:]=numpy.nan
                data=numpy.concatenate((padding,data))
            elif offsetStart>0:
                #left trimming is necessary
                data=data[offsetStart:]
            
        if endEpCut:
            if len(data)<expectedPoints:
                # right padding is necessary
                padding=numpy.empty(expectedPoints-len(data))
                padding[:]=numpy.nan
                data=numpy.concatenate((data,padding))
            elif len(data)>expectedPoints:
                # right trimming is necessary
                data=data[:expectedPoints]
            
        self.debug("data shape after cutting/padding: %s"%str(data.shape))
        
        if binsize:
            self.debug("binning to %s"%binsize,5)
            binSamples=int(binsize/self.secPerLine) #number of samples per bin
            self.secPerLine2=self.secPerLine*binSamples #seconds per sample
            if len(data) % binSamples: # we need to extend this to the appropriate bin size               
                hangover=len(data) % binSamples
                needed=numpy.empty(binSamples-hangover)
                needed[:]=numpy.NaN
                data=numpy.append(data,needed)
            data=numpy.reshape(data,(len(data)/binSamples,binSamples))      
            #data=numpy.ma.masked_invalid(data).mean(axis=1) #this is bad because it makes NaN become 0
            #data=numpy.mean(data,axis=1) #now it's binned!
            
            ### THIS PART IS NEW #################################
            avgs=numpy.empty(len(data))
            for i in range(len(data)):
                line=data[i]
                line=line[numpy.where(numpy.isfinite(line))[0]]
                avgs[i]=numpy.average(line)
            data=avgs       
            ######################################################
            
        self.debug("data shape at end of binning: %s"%str(data.shape))
        
        if sweep:
            self.debug("sweeping",5)
            samplesPerDay=int(60*60*24/self.secPerLine2)
            if len(data) % samplesPerDay: # we need to extend this to the appropriate bin size               
                hangover=len(data) % samplesPerDay
                needed=numpy.empty(samplesPerDay-hangover)
                needed[:]=numpy.nan
                data=numpy.append(data,needed)
            days=len(data)/float(samplesPerDay)       
            data=numpy.reshape(data,(int(days),int(len(data)/days)))
            xs=numpy.arange(0,24.0,24.0/float(len(data[0])))
        else:
            #data=numpy.array([data])
            data=numpy.atleast_2d(data)
            xs=range(int(startEpCut),int(startEpCut+self.secPerLine2*len(data[0])),int(self.secPerLine2))
            for i in range(len(xs)): xs[i]=ep2dt(xs[i])

        self.debug("data shape at end of sweeping: %s"%str(data.shape))            
            
        if numpy.max(data)==0 or numpy.ma.count(data)==0:
            self.debug("%s - %s - NO DATA!"%(animal,feature),2)
            return []
        
        self.debug("returning data of size: %d"%len(data[0]))
        return [xs,data,startEpCut,startEpCut+self.secPerLine2*len(data[0])]
    
    
    #######################
    ### DATA STATISTICS ###
    #######################
        
    def dataAverage(self,data):
        """Given [[ys],[ys],[ys]] return [avg,err]. If stderr=False, return stdev."""                 
        if data is None or not data.any():
            self.debug("averager got None value",5)
            return [[],[]]
        if len(data)==1:
            self.debug("only a single data stream, nothing to average",5)
            return [data[0],numpy.zeros(len(data[0]))]
        avg=numpy.mean(numpy.ma.masked_invalid(data),axis=0)
        err=numpy.std(numpy.ma.masked_invalid(data),axis=0)              
        cnt=numpy.isfinite(data).sum(0)
        if self.scheme["stdev"]==False: 
            err=err/numpy.sqrt(cnt)    #standard error
        if numpy.sum(numpy.isfinite(data))==0:
            self.debug("Averager got nothing but NaN. Giving back NaN.",5)
            avg[:]=numpy.NaN
            err[:]=numpy.NaN

        avg[numpy.ma.getmask(avg)]=numpy.nan
        err[numpy.ma.getmask(err)]=numpy.nan

        return [avg,err]
            
    
    #################
    ### ANALYSIS  ###
    #################
    
    def dataClear(self):
        """reset data={} where format is as follows:
            
            data["feature"]=[x,E,ER,[Es,Es,Es],B,BR,[Bs,Bs,Bs],N]
            
            where:
                
                x  - experiment x time points         
                E  - experiment average trace
                ER - experiment average error
                Es - experiment individual traces    
                
                x2 - baseline x time points
                B  - baseline average trace
                BR - baseline average error
                Bs - baseline individual traces
                
                N  - normalized value (E-B) +/ ER
                     In reality, are better stats necesary???
            
            """

        self.data={}
    
    def schemeExecute(self):
        self.schemeShow()
        self.debug("executing analysis",2)
        self.schemeRecalculate()
        self.dataClear()
        self.processing=True
        animals=com2lst(self.scheme["animals"])
        features=com2lst(self.scheme["features"])        
        timeExecuteStart=time.time()

        if not os.path.exists(self.scheme["output"]):
            os.makedirs(self.scheme["output"])
          
        # data["feature"]=[x,E,ER,Es, x2,B,BR,Bs,N,NR]
        #                  0 1 2  3   4  5 6  7  8 9  



        #dataLine=[x,Eavg,Eerr,linearEs,x2,Bavg,Berr,linearBs,norm,normErr]
        x,Eavg,Eerr,linearEs,x2,Bavg,Berr,linearBs,norm,normErr=[None]*10
                     
        for i in range(len(features)):           
            linearEs=numpy.empty((len(animals),self.scheme["expPoints"]))
            linearEs[:]=numpy.NaN        
            linearBs=numpy.empty((len(animals),self.scheme["basePoints"]))
            linearBs[:]=numpy.NaN           
            
            for j in range(len(animals)):
                feature=features[i]
                animal=animals[j]
                progress=len(animals)*i+j                    
                if self.uimain and self.app: 
                    if self.abortNow==True:
                        self.abortNow=False
                        return
                    self.uimain.progExecute.setMaximum(len(features)*len(animals))
                    self.uimain.progExecute.setValue(progress+1)
                    self.uimain.lblStatus.setText("processing %s - %s"%(animal,feature))
                    self.app.processEvents()             
                dataLine=[None]*9
                dataPack=self.loadData(animal,feature,self.scheme["location"],st2ep(self.scheme["expA"]),st2ep(self.scheme["expB"]),int(self.scheme["binsize"]),self.scheme["sweep"])
                if len(dataPack)>0:
                    x,Es,timeA,timeB=dataPack
                    EsweepAvg,EsweepErr=self.dataAverage(Es)
                    if len(animals)==1:
                        Eavg,Eerr=EsweepAvg,EsweepErr
                        linearEs=Es
                    else:
                        linearEs[j][:]=EsweepAvg
                if self.scheme["baseline"]==True: 
                    dataPack=self.loadData(animal,feature,self.scheme["location"],st2ep(self.scheme["baseA"]),st2ep(self.scheme["baseB"]),int(self.scheme["binsize"]),self.scheme["sweep"])
                    if len(dataPack)>0:
                        x2,Bs,baseA,baseB=dataPack
                        BsweepAvg,BsweepErr=self.dataAverage(Bs)
                        if len(animals)==1:
                            Bavg,Berr=BsweepAvg,BsweepErr
                            linearBs=Bs
                        else:
                            linearBs[j]=BsweepAvg                
                pass # last thing to do for each animal
            
            if len(animals)>1:
                Eavg,Eerr=self.dataAverage(linearEs)
                Bavg,Berr=self.dataAverage(linearBs)
  
            if self.scheme["baseline"]==True:
                if len(Eavg)==len(Bavg):
                    norm=Eavg-Bavg
                    normErr=numpy.sqrt(Eerr*Eerr+Berr*Berr)              
                else:
                    self.debug("can't create baseline because lengths are uneven.")
                  
            dataLine=[x,Eavg,Eerr,linearEs,x2,Bavg,Berr,linearBs,norm,normErr]
            self.data[feature]=dataLine
            pass #last thing to do for each feature
                
        timeExecute=time.time()-timeExecuteStart
        self.debug("scheme analyzed in %.03f seconds."%timeExecute,3)
        if self.uimain and self.app:
            if self.abortNow==True:
                self.abortNow=False
                return
            self.uimain.lblStatus.setText("scheme analyzed in %.03f seconds."%timeExecute)
            self.uimain.progExecute.setMaximum(len(features)*len(animals))
            self.uimain.progExecute.setValue(0)
    
    
    #####################
    ### DATA PLOTTING ###
    #####################
    
    def plotPopup(self):
        self.uimain.btnLaunchInteractive.setEnabled(False)
        self.plotFigure()
        pylab.show()
        self.uimain.btnLaunchInteractive.setEnabled(True)
    
    def summaryPopup(self):
        self.schemeRecalculate()
        self.uimain.btnSummary.setEnabled(False)
        self.plotSummary()
        pylab.show()
        self.uimain.btnSummary.setEnabled(True)
    
    def plotSummary(self,fig=None):
        """plots summary figure for all animals in the current folder."""
        self.debug("generating plot summary figure...",3)
        if not fig: fig=pylab.figure()
        axes=fig.gca()       
        selAnimals=com2lst(self.scheme["animals"])
        for i in range(len(selAnimals)):
            self.debug("generating plot summary figure... plotting animal %d of %d"%(i,len(selAnimals)),3)
            animal=selAnimals[i]
            feature=com2lst(self.scheme["features"])[0]
            data=self.loadData(animal,feature,binsize=60*60,sweep=False)
            if len(data)==0: continue
            xs,data,startX,endX=data
            ys=data[0]*0
            ys=ys+i
            axes.plot(xs,ys,'.')

        for spine in axes.spines.itervalues():
            spine.set_visible(False)
                   
        axes.set_yticklabels(selAnimals)
        axes.yaxis.set_major_locator(matplotlib.ticker.FixedLocator(range(len(selAnimals))))
        
        for xlabel in axes.get_xaxis().get_ticklabels():           
            xlabel.set_rotation(90)   
        fig.subplots_adjust(bottom=.35,left=.08, right=0.98) 
        fig.set_facecolor("#FFFFFF")            
        axes.set_title("DATA SUMMARY")
        
        
        axes.autoscale()
        axes.set_ylim((-.5,i+1.5))
        x1,x2=axes.get_xlim()
        x1=x1-3
        x2=x2+3
        axes.set_xlim((x1,x2))

        if self.scheme["baseline"]:
            axes.axvspan(st2dt(self.scheme["baseA"]),st2dt(self.scheme["baseB"]),facecolor="b",alpha=.1)
            axes.text(ep2dt((st2ep(self.scheme["baseA"])+st2ep(self.scheme["baseB"]))/2),i+1,"baseline",color='blue',horizontalalignment='center',verticalalignment='top')
        axes.axvspan(st2dt(self.scheme["expA"]),st2dt(self.scheme["expB"]),facecolor="g",alpha=.1)
        axes.text(ep2dt((st2ep(self.scheme["expA"])+st2ep(self.scheme["expB"]))/2),i+1,"experiment",color='green',horizontalalignment='center',verticalalignment='top')
        self.debug("generating plot summary figure... COMPLETE!",3)
        return fig        
        
    def plotFigure(self,figure=None):
        """given a figure and data key, make a pretty telemetry graph."""
        if not figure: figure=pylab.figure()
        axes=figure.gca()
        key=self.scheme["plotKey"]
        self.debug("plotting data for key %d (%s)"%(key,self.data.keys()[key]),3)
        key=self.data.keys()[key]
        d=self.data[key]
        
        if self.scheme["plotSecondary"]==True:
            if numpy.array(d[3]).any and self.scheme["plotExperiment"]:
                for yvals in d[3]: 
                    # SECONDARY EXPERIMENTAL
                    axes.plot(d[0],yvals,'g-',alpha=.2)
            if numpy.array(d[7]).any and self.scheme["baseline"] and self.scheme["plotBaseline"]:
                    for yvals in d[7]:
                        # SECONDARY BASELINE
                        axes.plot(d[4],yvals,'b-',alpha=.2)

        if self.scheme["plotPrimary"]==True:
            if numpy.array(d[1]).any and self.scheme["plotExperiment"]:    
                # PRIMARY EXPERIMENTAL
                axes.plot(d[0],d[1],'g-',label="experiment")
            if numpy.array(d[5]).any and self.scheme["baseline"] and self.scheme["plotBaseline"]:   
                # PRIMARY BASELINE
                axes.plot(d[4],d[5],'b-',label="baseline")

        if self.scheme["plotNormalized"] and d[8]:
                # NORMALIZED
                axes.plot(d[0],d[8],'r-')

        if self.scheme["plotErrorBars"]==True:
            if numpy.array(d[1]).any and self.scheme["plotExperiment"]:           
                # EXPERIMENTAL ERROR BARS
                axes.errorbar(d[0],d[1],yerr=d[2],fmt='g.')
            if numpy.array(d[5]).any and self.scheme["baseline"] and self.scheme["plotBaseline"]:            
                # BASELINE ERROR BARS
                axes.errorbar(d[4],d[5],yerr=d[6],fmt='b.')
            if numpy.array(d[8]).any and self.scheme["plotNormalized"]==True:
                # NORMALIZED ERROR BARS
                axes.errorbar(d[0],d[8],yerr=d[9],fmt='r.')

        for xlabel in axes.get_xaxis().get_ticklabels(): 
            #TODO make labels offset by the 24 hour day start time            
            xlabel.set_rotation(90)   
            
        axes.set_title("%s - %s"%(self.scheme["animals"],key))
        axes.grid()
        figure.subplots_adjust(bottom=.35,left=.08, right=0.98) 
        figure.set_facecolor("#FFFFFF")      
        if self.scheme["sweep"]: axes.set_xlim([0,24])
        
        #figure.canvas.draw()
        return figure
    
    

    ###################
    ### DATA OUTPUT ###
    ###################    

    # data["feature"]=[x,E,ER,Es, x2,B,BR,Bs,N,NR]
    #                  0 1 2  3   4  5 6  7  8 9      
    
    def outputHTML(self,launchItToo=True):
        self.outputImages()
        out='<html><body><div align="center">'
        out+="<h1>Telem-A-Gator</h2>"
        out+="<h2>Summary Report</h2>"
        
        out+='<img src="summary.png"><br>'
        keys=self.data.keys()
        for i in range(len(keys)):
            out+='<img src="%s"><br>'%(keys[i]+".png")
        
        out+="<h2>Scheme Data:</h2>"
        out+=self.scheme2txt(self.scheme).replace("\n","<br>")
        out+="</div></body></html>"
        f=open(os.path.join(self.scheme["output"],"summary.html"),'w')
        f.write(out)
        f.close()
        
        if launchItToo:
            cmd="explorer.exe "+os.path.abspath(os.path.join(self.scheme["output"],"summary.html"))
            self.debug("running: "+cmd,3)
            threadCmd(cmd)
        
        
        return
    
    def outputImages(self):
        """save every feature in data{} as an image."""
        keys=self.data.keys()
        for i in range(len(keys)):
            self.debug("generating image for %s"%keys[i])
            self.scheme["plotKey"]=i
            self.plotFigure()
            self.debug("saving "+keys[i]+".png")
            pylab.savefig(os.path.join(self.scheme["output"],keys[i]+".png"))
            pylab.close()
        self.plotSummary()
        pylab.savefig(os.path.join(self.scheme["output"],"summary.png"))
        pylab.close()
        self.schemeSave(os.path.join(self.scheme["output"],"schemeUsed.ini"))
        self.debug("image export complete.")

    def generateCSV(self,dates,avg,err,sweeps,fname):
        """given some data, format it as a proper CSV file."""
        fout=os.path.join(self.scheme["output"],fname)
        #matrix=numpy.array([dates,avg,err,sweeps])

        if dates==None or avg==None: 
            #no data
            return

        animals=com2lst(self.scheme["animals"])

        rows=3 
        if sweeps: 
            rows+=len(sweeps)
        cols = len(avg)
        
        matrix=numpy.zeros((rows,cols),dtype=numpy.object)
        for i in range(len(dates)):
            if type(dates[i])<>float:
                dates[i]=str(dates[i])

        matrix[0,:len(dates)]=dates
        matrix[1,:len(avg)]=avg
        matrix[2,:len(err)]=err

        if sweeps:
            for i in range(len(sweeps)):
                matrix[3+i,:]=sweeps[i]

        matrix=numpy.rot90(matrix,1)
        matrix=matrix[::-1]
        labels=matrix[0]

        self.debug("saving %s"%(fname))
        out="Time,Average,Error"
        if sweeps:
            for i in range(len(sweeps)):
                if len(animals)>1:
                    out+=","+animals[i]
                else:
                    out+=",DAY %d"%(i+1)
        out+="\n"
        
        for line in matrix:
            line=line.tolist()
            for i in range(len(line)):
                line[i]=str(line[i])
                if line[i]=='nan':
                    line[i]=''
            out+=",".join(line)+"\n"

        f=open(fout,'w')
        f.write(out)
        f.close()
        self.schemeSave(os.path.join(self.scheme["output"],"schemeUsed.ini"))
        
    def outputExcel(self):
        """save every feature in data{} as an image."""
        keys=self.data.keys()
        for i in range(len(keys)):
            self.debug("generating Excel file for %s"%(keys[i]))
            dataLine=self.data[keys[i]]
            self.generateCSV(dataLine[0],dataLine[1],dataLine[2],dataLine[3],keys[i]+"-experiment.csv")
            self.generateCSV(dataLine[4],dataLine[5],dataLine[6],dataLine[7],keys[i]+"-baseline.csv")
            self.generateCSV(dataLine[0],dataLine[8],dataLine[9],None,keys[i]+"-normalized.csv")
        self.debug("Excel output complete.")
            
    ######################
    ### MISC PROCESSES ###
    ######################
    
    def makeCrashLog(self):
        sep="#"*20
        out=sep+" MOST RECENT SCHEME "+sep
        out="\n\n\n"+sep+" FULL LOG OUTPUT "+sep+"\n\n\n"
        #self.schemeShow()
        for line in self.log:
            t,l,m=line
            out+="[%s]%s%s\n"%(ep2st(t),"-"*l,m)
        fname="crashlog-%s.txt"%(ep2fn(time.time()))
        #fname="crashlog.txt"
        f=open('./log/'+fname,'w')
        f.write(out)
        f.close()
        messagebox("BUG REPORT","saved bug report as:\n"+fname)
        
    
    def debug(self,msg,level=3):
        """save messages to session log with optional significance.
        levels:
            1 - critical, show pop-up window, exit
            2 - critical, show pop-up window
            3 - important
            4 - casual
            5 - rediculous
        """
        self.log.append([time.time(),level,msg])

        if level<2:
            messagebox("IMPORTANT",msg)

        if level<=self.printLogLevel: 
            print " "*level+msg
            if self.uimain and self.app: 
                self.uimain.lblDebug.setText(shortenTo(msg.replace("\n","")))
                self.uimain.textDebug.appendPlainText(msg)
                self.app.processEvents()  

    def showDebug(self,maxLevel=5):
        for item in self.log:
            print item


if __name__ == "__main__":            
    print "DONT RUN ME DIRECTLY."
    TG=TelemSession()
#    TG.summaryPopup()
    TG.schemeLoad("SCOTT.ini")
    TG.schemeExecute()
    TG.plotFigure()
#    #TG.makeCrashLog()
    pylab.show()
