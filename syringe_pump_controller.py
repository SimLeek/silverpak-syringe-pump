#!/usr/bin/env python3
# vim: set expandtab tabstop=4:

import imp
try:
    imp.find_module('PyQt5')
    from PyQt5.QtCore import QObject, pyqtSignal
    from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
    from syringe_pump_controller_ui import Ui_MainWindow
    from syringe_pump_init_ui import Ui_InitWindow
except ImportError:
    try:
        imp.find_module('PyQt4')
        from PyQt4 import QtGui, QtCore
        from PyQt4.QtCore import pyqtSignal
        from PyQt4.QtGui import QApplication, QMainWindow, QDialog
        from syringe_pump_controller_ui import Ui_MainWindow
        from syringe_pump_init_ui import Ui_InitWindow

    except ImportError:
        print("Error: neither PyQt4 nor PyQt5 is installed.")
import silverpak
import optparse
import math
import threading
import xml.etree.ElementTree as ET
import time

class MotorData:
    def __init__(self, char):
        self.char=char
        self.motor_position=1073741823#(2^30)-1
        self.is_max_set=False
        self.is_min_set=False
        self.max_pos=2147483647#(2^31)-1
        #experimentally decent default calibration values
        self.mL_per_rad=0.016631691553103064
        self.motor_position_per_rad=8156.69083345965
        #last pump operations, for calibration reasons
        self.vol=0
        self.rad=0


class ControllerWindow(QMainWindow):
    """This class creats a dialogue window for interacting with the silverpak motor when it's part of a syringe pump. 
    
    Note: 
        Some information is saved to and read from the syringe_pump_data.xml file. Other higher priority information is proposed to be saved to and loaded from the syringe pump itself, however, that may require modifying silverpak.py.

    Raises:
        ValueError: Everything raises this if you don't type numbers.
    
    """

    #--------------#
    #INIT FUNCTIONS#
    #--------------#

    sig=pyqtSignal()
    def __init__(self):
        """Initializes the class, initializes the motor, and connects all the buttons."""
        super(ControllerWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #MOTOR INIT SECTION
        self.motor_position=0 #goes from 0 - (2^31)-1

        self.pump_char='1' #output to default pump
        self.parse_xml('syringe_pump_data.xml')

        self.motor = silverpak.Silverpak() #motor class with useful commands
        fail_text= "WARNING: No silverpak found, entering testing mode.\n"
        try:
            if not self.motor.findAndConnect(): #no motor found
                self.ui.console.appendPlainText(fail_text)
            
            warn = InitWindow(self) #warn users that motor turns on init
            warn.exec_()#stop until accepted

        except TypeError: #also no motor found
            self.ui.console.appendPlainText(fail_text)

        #BUTTON INIT SECTION
        self.ui.calibrate_pump_button.clicked.connect(self.handleCalibInject)
        self.ui.calibrate_button.clicked.connect(self.handleCalib)
        self.ui.inject_button.clicked.connect(self.handleInject)
        self.ui.pump_button.clicked.connect(self.handlePump)
        self.ui.STOP.clicked.connect(self.stop)         
        self.ui.RUN.clicked.connect(self.init_motor)

        self.ui.no_min_button.setChecked(True)
        self.ui.no_max_button.setChecked(True)
        self.is_max_set=True
        self.is_min_set=True
        self.max_pos=0
        try:
            self.no_max()
            self.no_min()
            self.show_max_draw()
            self.show_max_inject()
            self.checkStatus()
        except AttributeError:
            #in case of testing mode, motor errors need to be ignored
            pass
        self.ui.set_min_button.stateChanged.connect(self.set_min)
        self.ui.set_max_button.stateChanged.connect(self.set_max)
        self.ui.no_min_button.stateChanged.connect(self.no_min)
        self.ui.no_max_button.stateChanged.connect(self.no_max)

        self.ui.cal_by_vol_radio.clicked.connect(self.set_test_volume_available)
        self.ui.cal_by_rot_radio.clicked.connect(self.set_test_rot_available)

        self.ui.pump_select.currentIndexChanged[str].connect(self.select_pump)
        self.ui.check_status_button.clicked.connect(self.checkStatus)
        self.ui.check_velocity_button.clicked.connect(self.checkVelocity)

    def init_motor(self):
        """Initializes the motor using the silverpak init command and sets valid velocity and acceleration values."""
        self.ui.console.appendPlainText("...")
        #default init command. Todo: allow user to set rotations allowed.
        self.motor.sendRawCommand("/"+self.pump_char+"Z10000R")
        while not self.motor.isReady():
            pass
        #Acceleration. Needed for motor to actually move.
        self.motor.sendRawCommand("/"+self.pump_char+"L5000R")
        while not self.motor.isReady():
            pass
        #Velocity. Needs to be set low for motor to move without slipping.
        self.motor.sendRawCommand("/"+self.pump_char+"V200000R")
        while not self.motor.isReady():
            pass
        self.ui.console.appendPlainText("Motor initialized.")

    def accept_init(self):
        """Acts as a QT slot for the InitWindow class. User selected init motor."""
        self.init_motor()

    def reject_init(self):
        """Acts as a QT slot for the InitWindow class. Testing mode means testing only gui."""
        self.ui.console.appendPlainText("Initialization rejected. Entering testing mode.")
        self.motor=None

    def pass_init(self):
        """Acts as a QT slot for the InitWindow class. Skips motor initialization when initializing window"""
        pass

#    def read(self, text):
#        """Reads from the UI console. Can replace the main console. I'm not sure if this works, but currently there is no need for it."""
#
#        #self.ui.plainTextEdit.insertPlainText(text)
#        text_read = ""
#        while self.ui.plainTextEdit.toPlainText[-1] != str('\0'):
#            text_read.append(self.ui.plainTextEdit.toPlainText[-1])
#        return text_read
#
#    def flush(self):
#        """Flushes the UI window console."""
#        pass

    #---------------#
    #DISPLAY HELPERS#
    #---------------#

    def set_test_volume_available(self):
        self.ui.cal_by_vol_unit.setEnabled(True)
        self.ui.cal_by_vol_num.setEnabled(True)
        self.ui.act_vol_unit.setEnabled(True)
        self.ui.act_vol_num.setEnabled(True)
        self.ui.cal_by_rot_unit.setEnabled(False)
        self.ui.cal_by_rot_num.setEnabled(False)
        self.ui.act_rot_unit.setEnabled(False)
        self.ui.act_rot_num.setEnabled(False)

    def set_test_rot_available(self):
        self.ui.cal_by_vol_unit.setEnabled(False)
        self.ui.cal_by_vol_num.setEnabled(False)
        self.ui.act_vol_unit.setEnabled(False)
        self.ui.act_vol_num.setEnabled(False)
        self.ui.cal_by_rot_unit.setEnabled(True)
        self.ui.cal_by_rot_num.setEnabled(True)
        self.ui.act_rot_unit.setEnabled(True)
        self.ui.act_rot_num.setEnabled(True)


    def show_max_draw(self):
        """Sets all three of the max draw indicators to the specified value.
        
        input:
            max_draw (float): the maximum volume available to draw, in mL. 
        
        """

        max_draw=(-self.motor_position/self.motor_position_per_rad)*self.mL_per_rad

        self.ui.max_draw_i.setText(str(max_draw))
        self.ui.max_draw_p.setText(str(max_draw))
        self.ui.max_draw_c.setText(str(max_draw))

    def show_max_inject(self):
        """Sets all two of the max draw indicators to the specified value.
        
        input:
            max_inject (float): the maximum volume available to inject, in mL. 
        
        """

        max_inject=((self.max_pos-self.motor_position)/self.motor_position_per_rad)*self.mL_per_rad

        self.ui.max_inject_i.setText(str(max_inject))
        self.ui.max_inject_c.setText(str(max_inject))

    #------------------#
    #DATA SERIALIZATION#
    #------------------#

    def parse_xml(self, filename):
        """Gets serialized data that may change between motors.

        Args:
            filename (str): name of the xml file to parse

        Raises:
            ValueError, ParseError

        """
        
        self.xml_good=True

        #scan doc
        try:
            tree=ET.parse(filename)
            root=tree.getroot()

            for child in root:
                if child.tag=='mL_per_rad':
                    self.mL_per_rad=float(child.text)
                elif child.tag=='pos_per_rad':
                    self.motor_position_per_rad=float(child.text)

        except EnvironmentError:
            pass

        #check data
        if not hasattr(self,'mL_per_rad'):
            self.mL_per_rad=0.016631691553103064#found experimentally
            self.xml_good=False
        if not hasattr(self,'pos_per_rad'):
            self.motor_position_per_rad=8156.69083345965#found experimentally(on free motor)
            self.xml_good=False

        #fix doc
        if not self.xml_good:
            self.ui.calib_default_radio.setChecked(True)
            self.write_xml(filename)
        else:
            self.ui.calib_default_radio.setChecked(False)

        self.ui.calib_ml_per_rad_line.setText(str(self.mL_per_rad))
        self.ui.calib_pos_per_rad_line.setText(str(self.motor_position_per_rad))

    def write_xml(self,filename):
        """Serializes data that may change between motors.

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
        pos_per_rad.text=str(self.motor_position_per_rad)

        #write xml
        tree=ET.ElementTree(root)
        tree.write(filename)

        #update calibration display data
        self.ui.calib_default_radio.setChecked(False)
        self.ui.calib_ml_per_rad_line.setText(str(self.mL_per_rad))
        self.ui.calib_pos_per_rad_line.setText(str(self.motor_position_per_rad))

    #--------------------#
    #CHANGE PUMP SETTINGS#
    #--------------------#

    def select_pump(self, text):
        """Selects which pump the class will be outputting to.
        
        Args:
            text: text from the dropdown menu with all possible motor names.

        """
        if text=='Pump 0':
            self.pump_char='@'
        elif text=='Pump 1':
            self.pump_char='1'
        elif text=='Pump 2':
            self.pump_char='2'
        elif text=='Pump 3':
            self.pump_char='3'
        elif text=='Pump 4':
            self.pump_char='4'
        elif text=='Pump 5':
            self.pump_char='5'
        elif text=='Pump 6':
            self.pump_char='6'
        elif text=='Pump 7':
            self.pump_char='7'
        elif text=='Pump 8':
            self.pump_char='8'
        elif text=='Pump 9':
            self.pump_char='9'
        elif text=='Pump A':
            self.pump_char=':'
        elif text=='Pump B':
            self.pump_char=';'
        elif text=='Pump C':
            self.pump_char='<'
        elif text=='Pump D':
            self.pump_char='='
        elif text=='Pump E':
            self.pump_char='>'
        elif text=='Pump F':
            self.pump_char='?'
        print(self.pump_char)

        self.ui.console.appendPlainText("Motor number changed. If the motor did not turn at program startup, please re-initialize.")

    def no_max(self):
        """Sets the motor value to somewhere near the middle of possible motor positions."""
        if self.is_max_set:
            self.motor_position=1073741824+self.motor_position
            self.motor.sendRawCommand("/"+self.pump_char+"z"+str(self.motor_position)+"R")
            self.max_pos=1073741824+self.max_pos
            self.ui.no_max_button.setChecked(True)
            self.ui.set_max_button.setChecked(False)
            self.is_max_set=False
            self.ui.set_min_button.setChecked(self.is_min_set)
            self.ui.no_min_button.setChecked(not self.is_min_set)

            self.show_max_draw()
            self.show_max_inject()

    def set_max(self):
        """Sets the current position to the maximum cc."""
        if not self.is_max_set:
            self.max_pos=abs(self.max_pos-self.motor_position)
            self.motor_position=0
            self.motor.sendRawCommand("/"+self.pump_char+"z0R")
            self.ui.set_max_button.setChecked(True)
            self.ui.no_max_button.setChecked(False)
            self.is_max_set=True
            self.ui.set_min_button.setChecked(self.is_min_set)
            self.ui.no_min_button.setChecked(not self.is_min_set)

            self.show_max_draw()
            self.show_max_inject()

    def set_min(self):
        """Sets the current position to the minimum cc."""
        if not self.is_min_set:
            self.max_pos=self.getPosition()
            self.ui.set_min_button.setChecked(True)
            self.ui.no_min_button.setChecked(False)
            self.is_min_set=True
            self.ui.set_max_button.setChecked(self.is_max_set)
            self.ui.no_max_button.setChecked(not self.is_max_set)

            self.show_max_draw()
            self.show_max_inject()

    def no_min(self):
        """Sets the max position to a high value that you'll never reach."""
        if self.is_min_set:
            self.max_pos=2147483647#(2^31)-1
            self.ui.no_min_button.setChecked(True)
            self.ui.set_min_button.setChecked(False)
            self.is_min_set=False
            self.ui.set_max_button.setChecked(self.is_max_set)
            self.ui.no_max_button.setChecked(not self.is_max_set)

            self.show_max_draw()
            self.show_max_inject()
   
   #-------------------------#
   #IMPORTANT MOTOR FUNCTIONS#
   #-------------------------#

    def checkVelocity(self):
        """Checks and reports if the motor is running at the correct velocity.
        
        Note:
            This function may not be useful for motors with no encoder wheels.
        """
        pos1txt=self.motor.sendRawCommand("/"+self.pump_char+"?0")
        t1=time.clock()
        pos2txt=self.motor.sendRawCommand("/"+self.pump_char+"?0")
        t2=time.clock()

        p1=[int(s) for s in pos1txt.split('\x00') if s.isdigit()]
        p2=[int(s) for s in pos2txt.split('\x00') if s.isdigit()]

        print(pos1txt)
        print(pos2txt)
        print(t1)
        print(t2)
        print(p1[0])
        print(p2[0])

        vMeasured=(p2[0]-p1[0])/(t2-t1)#measure velocity in microsteps / sec

        vReptxt=self.motor.sendRawCommand("/"+self.pump_char+"?2")

        vRep=[int(s) for s in vReptxt.split('\x00') if s.isdigit()]
        vReported=vRep[0]

        if vMeasured>0:
            direction="injecting"
        else:
            direction="drawing"

        #check if velocity is withing 5% of reuested
        if vMeasured==0:
            self.ui.console.appendPlainText("motor is not moving.")
        elif (abs(vMeasured)-vReported) < 0.05*vReported:
            percent=100*((abs(vMeasured)-vReported)/vReported)
            self.ui.console.appendPlainText("Motor is safely "+direction+" within "+str(percent)+"% of requested velocity (R:"+str(vReported)+",M:"+str(vMeasured)+")")
        else:
            percent=100*((abs(vMeasured)-vReported)/vReported)
            self.ui.console.appendPlainText("Motor is unsafely "+direction+" "+str(percent)+"% off from requested velocity (R:"+str(vReported)+",M:"+str(vMeasured)+")")
            self.ui.console.appendPlainText("Please check again in case this query was run during a start or stop operation.")



    def checkStatus(self):
        """Checks if the motor is working"""
        motor_name=self.motor.sendRawCommand("/"+self.pump_char+"&")

        if motor_name==None:
            self.ui.console.appendPlainText("Motor did not respond.")
        else:
            self.ui.console.appendPlainText("Motor: "+motor_name+" is working.")

    def getPosition(self):
        """Gets the current position of the motor
        
        Returns:
            the position of the motor in steps from 0.
        Raises:
            AttributeError: if motor is not responding correctly

        """
        txt=self.motor.sendRawCommand("/"+self.pump_char+"?0")
        #print(str(txt))
        n=[int(s) for s in txt.split('\x00') if s.isdigit()]
        #print(n)

        return int(n[0])

    def stop(self):
        """Stops the motor."""
        self.motor.sendRawCommand("/"+self.pump_char+"TR")
        self.motor_position=self.getPosition()

        self.show_max_draw()
        self.show_max_inject()

    #--------------#
    #MAIN FUNCTIONS#
    #--------------#

    def handlePump(self):
        """Sets up a loop of inject, pause, draw, pause, and repeat n times to the motor"""
        #get info
        self.vol=float(self.ui.pumping_vol_num.text())
        no_pumps=float(self.ui.pumping_pumps_num.text())
        pull_time=float(self.ui.pumping_pull_time_num.text())
        top_wait_time=float(self.ui.pumping_top_wait_time_num.text())
        push_time=float(self.ui.pumping_push_time_num.text())
        bottom_wait_time=float(self.ui.pumping_bottom_wait_time_num.text())
        
        #check info
        if self.vol<0 or no_pumps<0 or pull_time<0 or top_wait_time<0 or push_time<0 or bottom_wait_time<0:
            self.ui.console.appendPlainText("err: negative values not allowed.")
            return

        #convert info
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
            
        self.rad = self.vol/self.mL_per_rad
        pos1=self.motor_position
        pos2=self.motor_position-self.rad*self.motor_position_per_rad

        #check info again...
        if pos2<0:
            self.ui.console.appendPlainText("warn: could not go past 0 position. Volume will not be as specified!")
            pos2=0

        #Impossible. Pumping cycle always starts by drawing.
        #if pos1>self.max_pos:
        #    self.ui.console.appendPlainTest("Warn: could not go past max position. Volume will not be as specififed!")

        pull_vel=abs((self.rad*self.motor_position_per_rad)/pull_time)
        push_vel=abs((self.rad*self.motor_position_per_rad)/push_time)

        if pull_vel>732143 or push_vel>732143:
            self.ui.console.appendPlainText("err: motor is not accurate at high speeds.")
            return
        #wait time has a max of 30 seconds in the documentation
        #but the motors allow (4 lvl) nested loops for as many as 30000 repeats
        #This will give us a maximum wait time of 10 days. If a longer time is
        # needed, you can nest another loop for a max wait of 850 years.
        if top_wait_time>30000:
            top_wait_string="gM30000"
            div=top_wait_time//30000
            top_wait_string+="G"+str(int(div))
            mod=top_wait_time%30000
            top_wait_string+="M"+str(int(mod))
        else:
            top_wait_string="M"+str(int(top_wait_time))
        if bottom_wait_time>30000:
            bottom_wait_string="gM30000"
            bdiv=bottom_wait_time//30000
            bottom_wait_string+="G"+str(int(bdiv))
            bmod=bottom_wait_time%30000
            bottom_wait_string+="M"+str(int(bmod))
        else:
            bottom_wait_string="M"+str(int(top_wait_time))

        #Send!
        exe="/"+self.pump_char+"gV"+str(int(pull_vel))+"A"+str(int(pos2))+top_wait_string+"V"+str(int(push_vel))+"A"+str(int(pos1))+bottom_wait_string+"G"+str(int(no_pumps))+"R"
        print(exe)
        self.motor.sendRawCommand(exe)

        self.show_max_draw()
        self.show_max_inject()
        
    def handleInject(self):
        """Tells the motor to inject."""

        #get and convert user input
        #Honestly, I think I added too many units
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
        vel=(abs(self.rad*self.motor_position_per_rad)/time)

        #check user input
        if vel>732143:
            self.ui.console.appendPlainText("err: motor is not accurate at high speeds.")
            return
        
        #set velocity
        self.motor.sendRawCommand("/"+self.pump_char+"V"+str(int(vel))+"R")
        self.motor_position=self.getPosition()+self.rad*self.motor_position_per_rad
        #more checking...
        if self.motor_position <0:
            self.ui.console.appendPlainText("warn: could not go past 0 position.")
            self.motor_position=0
        if self.motor_position>self.max_pos:
            self.ui.console.appendPlainText("Warn: could not go past max position. Will not inject correct volume!")
            self.motor_position=self.max_pos

        #Inject!
        self.motor.sendRawCommand("/"+self.pump_char+"A"+str(int(self.motor_position))+"R")

        self.show_max_draw()
        self.show_max_inject()

    def handleCalibInject(self):
        """Exactly the same as inject, but more limited. After all, we don't want people calibrating with teaspoons, do we?"""

        #get and calculate input
        if self.ui.cal_by_vol_radio.isChecked():#by volume
            self.vol = float(self.ui.cal_by_vol_num.text())
            if str(self.ui.cal_by_vol_unit.currentText()) == "mL":
                pass
            self.rad = self.vol/self.mL_per_rad
        else:#by rotations
            self.vol=None
            self.rad = float(self.ui.cal_by_rot_num.text())
            if str(self.ui.cal_by_rot_unit.currentText()) == "degrees":
                self.rad = self.rad*(math.pi/180.)
            elif str(self.ui.cal_by_rot_unit.currentText()) == "radians":
                pass
            elif str(self.ui.cal_by_rot_unit.currentText()) == "no. rev.":
                self.rad= self.rad*(2*math.pi)
        
        self.motor_position=self.getPosition()+self.rad*self.motor_position_per_rad
        #check input
        if self.motor_position <0:
            self.ui.console.appendPlainText("warn: could not go past 0 position.  Volume will not be correct! Do not use to recalibrate!")
            self.motor_position=0
        elif self.motor_position>self.max_pos:
            self.ui.console.appendPlainText("Warn: could not go past max position. Volume will not be correct! Do not use to recalibrate!")
            self.motor_position=self.max_pos
        
        #send!
        self.motor.sendRawCommand("/"+self.pump_char+"A"+str(int(self.motor_position))+"R")

        self.show_max_draw()
        self.show_max_inject()

    def handleCalib(self):
        """Resets the motor constants."""

        #get and calculate input
        if self.ui.cal_by_vol_radio.isChecked():#volume
            actVol = float(self.ui.act_vol_num.text())
            if str(self.ui.cal_by_vol_unit.currentText()) == "mL":
                pass
            self.mL_per_rad=actVol/self.rad #compare to previous operation
            self.write_xml('syringe_pump_data.xml')
        else:#rotations
            actRad = float(self.ui.act_rot_num.text())
            if str(self.ui.act_rot_unit.currentText())=="degrees":
                actRad=actRad*(math.pi/180.)
            elif str(self.ui.act_rot_unit.currentText())== "radians":
                pass
            elif str(self.ui.act_rot_unit.currentText())=="no. rev.":
                actRad=actRad*(2*math.pi)
            self.motor_position_per_rad=(self.rad*self.motor_position_per_rad)/actRad #compare to previous operation
            self.write_xml('syringe_pump_data.xml')

        self.show_max_draw()
        self.show_max_inject()

class InitWindow(QDialog):
    """This window warns the user that initializing the motor may ruin their stuff, and gives them the option to do it or not."""

    def __init__(self, parent=None):
        """Creates the window and all of its UI.
        
        Input:
            parent: opener of this window. Preferrably ControllerWindow.
        Raises:
            AttributeError: parent doesn't have the QT slots for this class.

        """
        super(InitWindow, self).__init__()

        self.ui= Ui_InitWindow()
        self.ui.setupUi(self)
        self.ui.init_button.clicked.connect(parent.accept_init)
        self.ui.init_button.clicked.connect(self.close)
        self.ui.entertesting_button.clicked.connect(parent.reject_init)
        self.ui.entertesting_button.clicked.connect(self.close)
        self.ui.dontinit_button.clicked.connect(parent.pass_init)
        self.ui.dontinit_button.clicked.connect(self.close)


if __name__ == '__main__':
    import sys
    
    app = QApplication(sys.argv)
    
    wind = ControllerWindow()
    
#    input= wind.read
#    sys.stdout = wind
    
    wind.show()
    
    sys.exit(app.exec_())
    
    
