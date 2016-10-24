# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 11:21:17 2015

@author: Martin Friedl
"""

# for command-line arguments
import sys
import datetime
# Python Qt4 bindings for GUI objects
from PyQt4 import QtCore,QtGui, uic
# Numpy functions for image creation
import numpy as np
# Matplotlib Figure object
from matplotlib.figure import Figure
# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

class MyWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi('IVCurveGenerator.ui', self)
        
        #Set default values
        self.startVoltage = 0
        self.endVoltage = 3
        self.NPoints = 16
        self.duty = 3
        self.pulseFactor = 1.0
        self.CorrWavePts = 1
        self.saved = False
        self.filename = '.'
        
        # Connect up the buttons.
        self.pbOpen.clicked.connect(self.openDoc)
        self.pbSave.clicked.connect(self.saveDoc)
        self.pbSaveAs.clicked.connect(self.saveAsDoc)
        
        # Connect up the checkboxes
        self.cbInvert.stateChanged.connect(self.updateSetpoints)
        self.cbBack.stateChanged.connect(self.updateSetpoints)
        self.cbCorrWave.stateChanged.connect(self.updateSetpoints)
        
        # Connect combobox
        self.cbTestType.currentIndexChanged.connect(self.updateSetpoints)

        # Connect up input lines
        self.leStartV.editingFinished.connect(self.updateSetpoints)        
        self.leEndV.editingFinished.connect(self.updateSetpoints)
        self.leNPoints.editingFinished.connect(self.updateSetpoints)
        self.leDuty.editingFinished.connect(self.updateSetpoints)
        self.lePulseFact.editingFinished.connect(self.updateSetpoints)
        self.leCorrWavePts.editingFinished.connect(self.updateSetpoints)
        
        # Create validators to validate the inputs (ints or doubles)
        self.leStartV.setValidator(QtGui.QDoubleValidator())
        self.leEndV.setValidator(QtGui.QDoubleValidator())
        self.leNPoints.setValidator(QtGui.QIntValidator())    
        self.leDuty.setValidator(QtGui.QIntValidator())
        self.lePulseFact.setValidator(QtGui.QDoubleValidator())
        self.leCorrWavePts.setValidator(QtGui.QIntValidator())       
        
        #Apply defaults to line edit fields in GUI
        self.leStartV.setText(str(self.startVoltage))
        self.leEndV.setText(str(self.endVoltage))
        self.leNPoints.setText(str(self.NPoints))        
        self.leDuty.setText(str(self.duty))
        self.lePulseFact.setText(str(self.pulseFactor))       
        self.leCorrWavePts.setText(str(self.CorrWavePts))  
        
        #Add NavigationToolbar
        self.mplwidget.figure.set_dpi(150)
        self.mplwidget.mpl_toolbar = NavigationToolbar(self.mplwidget.figure.canvas, self.mplwidget)
        self.verticalLayout.setDirection(QtGui.QBoxLayout.BottomToTop)
        self.verticalLayout.addWidget(self.mplwidget.mpl_toolbar,1)

        self.mplwidget.myplot = self.mplwidget.figure.add_subplot(111)        
        self.mplwidget.myplot.set_title("Pulse Curve")
        self.mplwidget.myplot.set_xlabel("Pt Index")
        self.mplwidget.myplot.set_ylabel("Voltage (V)")  
        
        self.show()
        self.updateSetpoints()        
        
    def openDoc(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'Choose file to open', None, filter='*.iv')
        if fileName:
            self.filename = fileName
            print fileName
    def saveDoc(self):
        if self.filename is None:
            self.saveAsDoc()
        else:
            f = open(self.filename, 'w')
            f.write("# Created by IVFileGenerator - Martin Friedl\n")
            f.write("# "+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"\n")
            f.write('# startVoltage:%.2e' % self.startVoltage+'\n')
            f.write('# endVoltage:%.2e' % self.endVoltage+'\n')
            f.write('# NPoints:%i' % self.NPoints+'\n')
            f.write('# duty:%i' % self.duty+'\n')
            f.write('# cbBack:%i' % self.cbBack.checkState()+'\n')
            f.write('# cbInvert:%i' % self.cbInvert.checkState()+'\n')
            f.write('# corrWaveform:%i' % self.cbCorrWave.checkState()+'\n')
            f.write('# corrWavePts:%i' % self.CorrWavePts + '\n')
            for i in self.setPoints:
                f.write('%E' % i+'\n')
            f.close()            
            print "Saved to " + str(self.filename)
            
        
    def saveAsDoc(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, 'Choose save file name', self.filename, filter='*.iv')
        if fileName:
            self.filename = fileName
            self.saveDoc()

    def updateSetpoints(self):

        self.startVoltage = float(self.leStartV.text())        
        self.endVoltage = float(self.leEndV.text()) 
        self.NPoints = int(self.leNPoints.text())   
        self.duty = int(self.leDuty.text())         
        self.pulseFactor = float(self.lePulseFact.text())     
        
        yVals = np.linspace(self.startVoltage,self.endVoltage,self.NPoints)        

        if self.cbBack.checkState():
            yVals = np.append(yVals,yVals[0:-1][::-1]) #Reverse array and remove duplicate value where they are joined
        if self.cbInvert.checkState():
            yVals = np.append(-yVals[::-1][0:-1],yVals)

        self.leCorrWavePts.setEnabled(False)
        self.cbCorrWave.setEnabled(False)
        
        if (self.cbTestType.currentText() == "Pulsed AC")or(self.cbTestType.currentText() == "Pulsed DC"):
            self.leDuty.setEnabled(True)
            self.lePulseFact.setEnabled(False)          
            pulsedAC = False
            if self.cbTestType.currentText() == "Pulsed AC":
                self.lePulseFact.setEnabled(True)
                self.cbCorrWave.setEnabled(True)
                if self.cbCorrWave.checkState():
                    self.leCorrWavePts.setEnabled(True)                
                pulsedAC = True
            yAC = np.array([])
            dataPtsX = np.array([])
            dataPtsY = np.array([])
            for i in range(0,len(yVals)):
                for j in range(0,self.duty):
                     yAC = np.append(yAC, 0)
                yAC = np.append(yAC, yVals[i])
                dataPtsX = np.append(dataPtsX,len(yAC))                
                if pulsedAC: #If pulsed AC add the opposite pulse
                    yAC = np.append(yAC, -yVals[i]*self.pulseFactor)
                    if self.cbCorrWave.checkState(): #Add correction wave
                        polarity = 1
                        for k in range(1,int(self.leCorrWavePts.text())+1):
                            yAC = np.append(yAC, yVals[i]*self.pulseFactor/pow(2,k)*polarity)
                            polarity = polarity * -1
                dataPtsY = np.append(dataPtsY,yVals[i])
            yVals = yAC
            xVals = np.array(range(len(yVals)))+1            
        elif self.cbTestType.currentText() == "Linear":
            self.leDuty.setEnabled(False)
            self.lePulseFact.setEnabled(False)            
            xVals = np.array(range(len(yVals)))+1
            dataPtsX = xVals            
            dataPtsY = yVals            
        
        self.setPoints = yVals
        self.mplwidget.myplot.cla()
        self.mplwidget.myplot.plot(xVals,yVals,marker='.', linestyle='-', color='r')
        self.mplwidget.myplot.hold(True)
        self.mplwidget.myplot.plot(dataPtsX,dataPtsY,marker='.', linestyle=':', color='b')
        self.mplwidget.myplot.grid()
        self.mplwidget.figure.canvas.draw()          
        
if __name__ == '__main__':
    # Create the GUI application
    qApp = QtGui.QApplication(sys.argv)
    window = MyWindow()
    window.show() 
    # start the Qt main loop execution, exiting from this script
    # with the same return code of Qt application
    sys.exit(qApp.exec_()) 
    
    