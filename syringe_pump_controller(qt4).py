from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QApplication, QMainWindow
from syringe_pump_controller_ui_qt4 import Ui_MainWindow
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
        self.ui.pump_button.clicked.connect(self.handlePump)
        self.ui.STOP.clicked.connect(self.stop)
        self.ui.Reset_0_button.clicked.connect(self.reset_0)
        self.ui.Revers_button.clicked.connect(self.reverse)

        self.mL_per_rad=0.016631691553103064#found experimentally
        self.pos_per_rad=8156.690833459656#found experimentally (not accurate, found on free motor)

        self.pos=0

        self.vol=None
        self.rad=None

    def reset_0(self):
        self.motor.sendRawCommand("/1z0R")
    
    def reverse(self):
        if self.is_rev:
            self.motor.sendRawCommand("/1F0R")
            print("/1F0R")
            self.is_rev=False
        elif not self.is_rev:
            self.motor.sendRawCommand("/1F1R")
            print("/1F1R")
            self.is_rev=True

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

    def stop(self):
        self.motor.sendRawCommand("/1TR")

    def handlePump(self):
        self.vol=float(self.ui.pumping_vol_num.text())
        no_pumps=float(self.ui.pumping_pumps_num.text())
        pull_time=float(self.ui.pumping_pull_time_num.text())
        top_wait_time=float(self.ui.pumping_top_wait_time_num.text())
        push_time=float(self.ui.pumping_push_time_num.text())
        bottom_wait_time=float(self.ui.pumping_bottom_wait_time_num.text())

        if str(self.ui.pumping_vol_unit.currentText())=="mL":
            pass

        if str(self.ui.pumping_pumps_unit.currentText())=="num":
            pass
        elif str(self.ui.pumping_pumps_unit.currentText())=="K":
            no_pumps=no_pumps*1000
        elif str(self.ui.pumping_pumps_unit.currentText())=="K":
            no_pumps=no_pumps*1000000

        if str(self.ui.pumping_pull_time_unit.currentText())=="seconds":
            pass
        elif str(self.ui.pumping_pull_time_unit.currentText())=="minutes":
            pull_time=pull_time*60
        elif str(self.ui.pumping_pull_time_unit.currentText())=="minutes":
            pull_time=pull_time*3600

        if str(self.ui.pumping_top_wait_time_unit.currentText())=="seconds":
            top_wait_time=top_wait_time*1000
        elif str(self.ui.pumping_top_wait_time_unit.currentText())=="minutes":
            top_wait_time=top_wait_time*1000*60
        elif str(self.ui.pumping_top_wait_time_unit.currentText())=="hours":
            top_wait_time=top_wait_time*1000*3600

        if str(self.ui.pumping_push_time_unit.currentText())=="seconds":
            pass
        elif str(self.ui.pumping_push_time_unit.currentText())=="minutes":
            push_time=push_time*60
        elif str(self.ui.pumping_push_time_unit.currentText())=="minutes":
            push_time=push_time*3600

        if str(self.ui.pumping_bottom_wait_time_unit.currentText())=="seconds":
            bottom_wait_time=bottom_wait_time*1000
        elif str(self.ui.pumping_bottom_wait_time_unit.currentText())=="minutes":
            bottom_wait_time=bottom_wait_time*1000*60
        elif str(self.ui.pumping_bottom_wait_time_unit.currentText())=="hours":
            bottom_wait_time=v*1000*3600
            
        pos2=0
        self.rad = self.vol/self.mL_per_rad
        pos1=pos2+self.rad*self.pos_per_rad

        

        pull_vel=abs((self.rad*self.pos_per_rad)/pull_time)
        push_vel=abs((self.rad*self.pos_per_rad)/push_time)

        if pull_vel>732143 or push_vel>732143:
            self.ui.console.appendPlainText("err: motor is not accurate at high speeds.")
            return

        exe="/1gV"+str(int(pull_vel))+"A"+str(int(pos2))+"M"+str(int(top_wait_time))+"V"+str(int(push_vel))+"A"+str(int(pos1))+"M"+str(int(bottom_wait_time))+"G"+str(int(no_pumps))+"R"
        print(exe)
        self.motor.sendRawCommand(exe)
        
    
    def handleInject(self):
        self.vol = float(self.ui.inject_amount_num.text())
        time=float(self.ui.inject_time_num.text())
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
        if str(self.ui.injection_time_unit.currentText())=="seconds":
            pass
        elif str(self.ui.injection_time_unit.currentText())=="minutes":
            time=time*60
        elif str(self.ui.injection_time_unit.currentText())=="minutes":
            time=time*3600
        self.rad = self.vol/self.mL_per_rad
        vel=(abs(self.rad*self.pos_per_rad)/time)
        print(vel)
        if vel>732143:
            self.ui.console.appendPlainText("err: motor is not accurate at high speeds.")
            return
        self.motor.sendRawCommand("/1V"+str(int(vel))+"R")
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
	
	
