from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from syringe_pump_controller_ui import Ui_MainWindow
import silverpak
import optparse
import math
import threading

class ControllerWindow(QMainWindow):

    sig=pyqtSignal()

    def __init__(self):
        super(ControllerWindow, self).__init__()

        self.motor = silverpak.Silverpak()
        if not self.motor.findAndConnect():
            sys.exit("no silverpak found")
    
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
    
        self.ui.calibrate_pump_button.clicked.connect(self.handleCalibInject)
        self.ui.calibrate_button.clicked.connect(self.handleCalib)
        self.ui.inject_button.clicked.connect(self.handleInject)
        

        self.mL_per_rad=0.33/(2*math.pi)#guessed at
        self.pos_per_rad=8156.690833459656#found experimentally (not accurate, found on free motor)

        self.pos=0

        self.vol=None
        self.rad=None

    def init2(self):
        init_text="""To initialize, the motor must spin a few times.
Please setup your system so this will not ruin whatever you're doing, then press RUN."""
        
        self.ui.console.appendPlainText(init_text)
        self.ui.RUN.clicked.connect(self.init3)

    def init3(self):
        self.ui.console.appendPlainText("...")
        self.motor.sendRawCommand("/1Z10000R")
        while not self.motor.isReady():
            pass
        self.motor.sendRawCommand("/1L5000R")#needed for motor to actually move
        while not self.motor.isReady():
            pass
        self.motor.sendRawCommand("/1V200000R")
        while not self.motor.isReady():
            pass
        self.ui.console.appendPlainText("Motor initialized.")

        self.position=self.motor.position()
    
    def handleInject(self):
        self.vol = float(self.ui.inject_amount_num.text())
        if str(self.ui.injection_vol_unit.currentText())=="cc":
            pass
        elif str(self.ui.injection_vol_unit.currentText())=="mL":
            pass
        elif str(self.ui.injection_vol_unit.currentText())=="L":
            self.vol=self.vol*1000
        elif str(self.ui.injection_vol_unit.currentText())=="Gallons":
            self.vol=self.vol*3785.41
        elif str(self.ui.injection_vol_unit.currentText())=="Pints":
            self.vol=self.vol*473.176
        elif str(self.ui.injection_vol_unit.currentText())=="teaspoons":
            self.vol=self.vol*4.92892
        elif str(self.ui.injection_vol_unit.currentText())=="Buckets":
            self.vol=self.vol*3785.41*4
        self.rad = self.vol/self.mL_per_rad
        self.pos=self.pos+self.rad*self.pos_per_rad
        if self.pos <0:
            self.pos=0
        print(self.pos)
        self.motor.sendRawCommand("/1A"+str(int(self.pos))+"R")
        print("/1A"+str(int(self.pos))+"R")

    def handleCalibInject(self):
        if self.ui.cal_by_vol_radio.isChecked():
            self.vol = float(self.ui.cal_by_vol_num.text())
            if str(self.ui.cal_by_vol_unit.currentText()) == "mL":
                pass
            self.rad = self.vol/self.mL_per_rad
        else:#by rotations
            self.vol=None
            self.rad = float(self.ui.cal_by_rot_num.text())
            if str(self.ui.cal_by_rot_unit.currentText()) == u"°":
                self.rad = self.rad*(math.pi/180.)
            elif str(self.ui.cal_by_rot_unit.currentText()) == "θ":
                pass
            elif str(self.ui.cal_by_rot_unit.currentText()) == "no. rev.":
                self.rad= self.rad*(2*math.pi)
        print(self.motor.position(),self.rad*self.pos_per_rad)
        self.pos=self.pos+self.rad*self.pos_per_rad
        if self.pos <0:
            self.pos=0
        print(self.pos)
        self.motor.sendRawCommand("/1A"+str(int(self.pos))+"R")
        print("/1A"+str(int(self.pos))+"R")

    def handleCalib(self):
        if self.ui.cal_by_vol_radio.isChecked():
            actVol = float(self.ui.act_vol_num.text())
            if str(self.ui.cal_by_vol_unit.currentText()) == "mL":
                pass
            print("oldmLpr: "+str(self.mL_per_rad))
            self.mL_per_rad=actVol/self.rad
            print("newmLpr: "+str(self.mL_per_rad))
        else:#by rotations
            #rotations were entered
            actRad = float(self.ui.act_rot_num.text())
            if str(self.ui.act_rot_unit.currentText())==u"°":
                actRad=actRad*(math.pi/180.)
            elif str(self.ui.act_rot_unit.currentText())== "θ":
                pass
            elif str(self.ui.act_rot_unit.currentText())=="no. rev.":
                actRad=actRad*(2*math.pi)
            print("oldppr: "+str(self.pos_per_rad))
            self.pos_per_rad=(self.rad*self.pos_per_rad)/actRad
            print("newppr: "+str(self.pos_per_rad))
            

    def write(self, text):
        self.ui.plainTextEdit.insertPlainText(text)
    
    def read(self, text):
        self.ui.plainTextEdit.insertPlainText(text)
        text_read = ""
        while self.ui.plainTextEdit.toPlainText[-1] != str('\0'):
            text_read.append(self.ui.plainTextEdit.toPlainText[-1])
        return text_read
    def flush(self):
        pass

if __name__ == '__main__':
    import sys
    
    app = QApplication(sys.argv)
    
    wind = ControllerWindow()
    
    #input= wind.read
    #sys.stdout = wind
    
    wind.show()
    wind.init2()
    
    sys.exit(app.exec_())
	
	
