#!/usr/bin/env python3
# vim: set expandtab tabstop=4:

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from syringe_pump_controller_ui import Ui_MainWindow
import silverpak
import optparse
import math
import threading
import xml.etree.ElementTree as ET

class ControllerWindow(QMainWindow):
    """This class creats a dialogue window for interacting with the silverpak motor when its part of a syringe pump.

    Input - File: syringe_pump_data.xml
            Com:  silverpak motor (assumes first valid port is motor)

    Output- File: syringe_pump_data.xml
            Com:  silverpak motor

    """

    sig=pyqtSignal()

    def __init__(self):
        super(ControllerWindow, self).__init__()

         #<UI>
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
    
        #make buttons call functions
        self.ui.calibrate_pump_button.clicked.connect(self.handleCalibInject)
        self.ui.calibrate_button.clicked.connect(self.handleCalib)
        self.ui.inject_button.clicked.connect(self.handleInject)
        self.ui.pump_button.clicked.connect(self.handlePump)
        self.ui.STOP.clicked.connect(self.stop)
        self.ui.Reset_0_button.clicked.connect(self.reset_0)
        self.ui.Revers_button.clicked.connect(self.reverse)
        self.ui.RUN.clicked.connect(self.init_motor)

        #</UI>

        #<motor>
        self.parse_xml('syringe_pump_data.xml')

        self.motor = silverpak.Silverpak()
        fail_text= "WARNING: No silverpak found, entering testing mode.\n"
        try:
            if not self.motor.findAndConnect():
                self.ui.console.appendPlainText(fail_text)

            is_rev=self.motor.sendRawCommand("/1e1R")
            if isinstance(is_rev,str) and is_rev:
                print("motor rev",is_rev)
                self.is_rev=bool(int(self.motor.sendRawCommand("/1e1R")))
            else:
                print("default rev")
                self.is_rev=False
                #todo: next command should go here, but I need to test it.
            self.motor.sendRawCommand("/1F1R")

        except TypeError:
            print("No motor connected. Entering testing mode.")

            self.is_rev=False

        self.pos=0
        #</motor>

        init_text="""To initialize, the motor must spin a few times.
Please setup your system so this will not ruin whatever you're doing, then press RUN."""
        self.ui.console.appendPlainText(init_text)
        

    def parse_xml(self, filename):
        """This function gets serialized data that may change between motors.

        Args:
            filename (str): name of the xml file to parse

        Raises:
            ValueError, ParseError

        """
        
        self.xml_good=True

        try:
            tree=ET.parse(filename)
            root=tree.getroot()
            #if not root.tag=='constants'
            #    

            #scan doc
            for child in root:
                if child.tag=='mL_per_rad':
                    self.mL_per_rad=float(child.text)
                elif child.tag=='pos_per_rad':
                    self.pos_per_rad=float(child.text)

        except FileNotFoundError:
            pass

        #check data
        if not hasattr(self,'mL_per_rad'):
            self.mL_per_rad=0.016631691553103064#found experimentally
            self.xml_good=False
        if not hasattr(self,'pos_per_rad'):
            self.pos_per_rad=8156.69083345965#found experimentally(on free motor)
            self.xml_good=False

        #fix doc
        if not self.xml_good:
            self.ui.calib_default_radio.setChecked(True)
            self.write_xml(filename)
        else:
            self.ui.calib_default_radio.setChecked(False)

        self.ui.calib_ml_per_rad_line.setText(str(self.mL_per_rad))
        self.ui.calib_pos_per_rad_line.setText(str(self.pos_per_rad))
    
    def write_xml(self,filename):
        """This function serializes data that may change between motors.

        Args:
            filename (str): name of the xml file to parse

        Raises:
            ValueError, ParseError

        """
        #make xml
        root=ET.Element('constants')
        mL_per_rad=ET.SubElement(root, 'mL_per_rad')
        mL_per_rad.text=str(self.mL_per_rad)
        pos_per_rad=ET.SubElement(root, 'pos_per_rad')
        pos_per_rad.text=str(self.pos_per_rad)

        #write xml
        tree=ET.ElementTree(root)
        tree.write(filename)

        #update calib data
        self.ui.calib_default_radio.setChecked(False)
        self.ui.calib_ml_per_rad_line.setText(str(self.mL_per_rad))
        self.ui.calib_pos_per_rad_line.setText(str(self.pos_per_rad))

    def reset_0(self):
        """This resets the motor to position 0."""
        self.motor.sendRawCommand("/1z0R")
    
    def reverse(self):
        """This reverses the direction of the motor and saves the current direction to the motor and the running program."""
        if not self.is_rev:
            self.motor.sendRawCommand("/1F0R")
            self.motor.sendRawCommand("/1s1p1R")#store direction
            print("/1F0R")
            self.is_rev=False
        elif self.is_rev:
            self.motor.sendRawCommand("/1F1R")
            self.motor.sendRawCommand("/1s1p0R")
            print("/1F1R")
            self.is_rev=True 

    def init_motor(self):
        """This initializes the motor using the silverpak init command and sets valid velocity and acceleration values."""
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

    def getPosition(self):
        """This gets the current position of the motor
        
        Note: for some reason, this doesn't seem to work.
        """
        txt=self.motor.sendRawCommand("/1?0")
        print(str(txt))
        n=[int(s) for s in txt.split('\x00') if s.isdigit()]
        print(n)
        return int(n[0])

    def stop(self):
        """This stops the motor."""
        self.motor.sendRawCommand("/1TR")

    def handlePump(self):
        """This sets up a loop of inject, pause, draw, pause, and repeat n times to the motor"""
        self.vol=float(self.ui.pumping_vol_num.text())
        no_pumps=float(self.ui.pumping_pumps_num.text())
        pull_time=float(self.ui.pumping_pull_time_num.text())
        top_wait_time=float(self.ui.pumping_top_wait_time_num.text())
        push_time=float(self.ui.pumping_push_time_num.text())
        bottom_wait_time=float(self.ui.pumping_bottom_wait_time_num.text())

        if self.vol<0 or no_pumps<0 or pull_time<0 or top_wait_time<0 or push_time<0 or bottom_wait_time<0:
            self.ui.console.appendPlainText("err: negative values not allowed.")
            return

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
            
        pos2=self.getPosition()
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
        """This tells the motor to inject. Honestly, I think I put in too many units.
        input:
            ui.injection_vol_unit (str): unit of injection volume
            ui.injection_time_unit (str): unit of time length
            ui.inject_amount_num (str): injection volume
            ui.inject_time_num (str): injection time length
            """
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
        self.pos=self.getPosition()+self.rad*self.pos_per_rad
        if self.pos <0:
            self.ui.console.appendPlainText("warn: could not go past 0 position.")
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
        self.pos=self.getPosition()+self.rad*self.pos_per_rad
        if self.pos <0:
            self.ui.console.appendPlainText("warn: could not go past 0 position.")
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
            self.write_xml('syringe_pump_data.xml')
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
            self.write_xml('syringe_pump_data.xml')

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
    
    sys.exit(app.exec_())
    
    
