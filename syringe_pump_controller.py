#!/usr/bin/env python3
# vim: set expandtab tabstop=4:

import imp
try:
    imp.find_module('PyQt5')
    from PyQt5 import QtCore
    from PyQt5.QtCore import QObject, pyqtSignal
    from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
except ImportError:
    try:
        imp.find_module('PyQt4')
        from PyQt4 import QtGui, QtCore
        from PyQt4.QtCore import pyqtSignal
        from PyQt4.QtGui import QApplication, QMainWindow, QDialog
    except ImportError:
        print("Error: neither PyQt4 nor PyQt5 is installed.")
from syringe_pump_controller_ui import Ui_MainWindow
#from syringe_pump_init_ui import Ui_InitWindow
import syringe_motor
import optparse
import math
import threading
import time
import os
import serial

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
        #UI INIT
        super(ControllerWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        #MOTOR CLASS INIT
        self.motorGroup=syringe_motor.MotorGroup()
        self.motorGroup.load('syringe_pump_data.xml')
        try:
            try:
                self.motor=self.motorGroup.motordict.iteritems().next()
            except AttributeError:
                self.motor=next(iter(self.motorGroup.motordict.values()))
        except StopIteration:
            self.motor=None

        if self.motor==None:
            self.motor=syringe_motor.Motor()
            self.motorGroup.motordict['1']=self.motor 
        else:
            index=int(syringe_motor.convertToNum(self.motor.motor_address),16)
            
            index=index-1
            if index<0:
                index=15
            self.ui.pump_select.setCurrentIndex(index)
        #BUTTON INIT
        #main functions
        self.ui.calibrate_button.clicked.connect(self.handleCalib)
        self.ui.inject_button.clicked.connect(self.handleInject)
        self.ui.pump_button.clicked.connect(self.handlePump)

        self.ui.STOP.clicked.connect(self.stop)         
        self.ui.RUN.clicked.connect(self.init_motor)#now INIT on Connection tab
        
        #position limit defaults
        self.ui.no_min_button.setChecked(True)
        self.ui.no_max_button.setChecked(True)
        self.motor.is_max_set=True
        self.motor.is_min_set=True

        #position limits
        self.ui.set_min_button.stateChanged.connect(self.set_min)
        self.ui.set_max_button.stateChanged.connect(self.set_max)
        self.ui.no_min_button.stateChanged.connect(self.no_min)
        self.ui.no_max_button.stateChanged.connect(self.no_max)
 
        #secondary functions
        self.ui.pump_select.currentIndexChanged[str].connect(self.select_pump)
        self.ui.pumpnew_button.clicked.connect(self.new_pump)
        self.ui.pumpdelete_button.clicked.connect(self.delete_pump)
        self.ui.pumpswitch_button.clicked.connect(self.switch_pump)
        self.ui.port_select.currentIndexChanged[str].connect(self.select_port)
        self.ui.portscan_button.clicked.connect(self.scan_ports)
        self.ui.baud_select.currentIndexChanged[str].connect(self.select_baud)
        self.ui.check_status_button.clicked.connect(self.checkStatus)
        self.ui.check_velocity_button.clicked.connect(self.checkVelocity) 
        self.ui.cal_expect_unit.currentIndexChanged[str].connect(self.calResultUnit)

        #USER NOTIFICATION
        self.ui.console.appendPlainText("No motors connected yet. Use the connection tab to connect motors.")

    def init_motor(self):
        """Initializes the motor using the silverpak init command and sets valid velocity and acceleration values."""
       
        

        #notify
        self.ui.console.appendPlainText("...")

        #Acceleration. Needed for motor to actually move.
        self.motor.sendRawCommand("/"+self.motor.motor_address+"L5000R")
        #Velocity. Needs to be set low for motor to move without slipping.
        self.motor.sendRawCommand("/"+self.motor.motor_address+"V200000R")
        #default init command. Todo: allow user to set rotations allowed.
        self.motor.sendRawCommand("/"+self.motor.motor_address+"Z10000R")

        #go back to starting position. It's usually two rotations, so go back that amount.
        #zero="/"+self.motor.motor_address+"z"+str(int(self.motor.motor_position_per_rad*2*math.pi))+"R"
        #print(zero)
        #self.motor.sendRawCommand(zero)
        #self.motor.sendRawCommand("/"+self.motor.motor_address+"A0R")

        #set the position limits so motor can move in both directions
        self.motor.max_pos=0
        
        self.no_max()
        self.no_min()
        self.show_max_draw()
        self.show_max_inject()
        self.checkStatus()

        self.ui.calib_ml_per_rad_line.setText(str(self.motor.mL_per_rad))
        self.ui.calib_pos_per_rad_line.setText(str(self.motor.motor_position_per_rad))

        #done
        self.ui.console.appendPlainText("Motor initialized.")

    #---------------#
    #DISPLAY HELPERS#
    #---------------#

    def show_max_draw(self):
        """Sets all three of the max draw indicators to the specified value.
        
        input:
            max_draw (float): the maximum volume available to draw, in mL. 
        
        """

        max_draw=(-self.motor.motor_position/self.motor.motor_position_per_rad)*self.motor.mL_per_rad

        self.ui.max_draw_i.setText(str(max_draw))
        self.ui.max_draw_p.setText(str(max_draw))
        self.ui.max_draw_c.setText(str(max_draw))

    def show_max_inject(self):
        """Sets all two of the max draw indicators to the specified value.
        
        input:
            max_inject (float): the maximum volume available to inject, in mL. 
        
        """

        max_inject=((self.motor.max_pos-self.motor.motor_position)/self.motor.motor_position_per_rad)*self.motor.mL_per_rad

        self.ui.max_inject_i.setText(str(max_inject))
        self.ui.max_inject_c.setText(str(max_inject))

    def calResultUnit(self, text):
        self.ui.cal_expect_unit_label.setText(text)

    #------------------#
    #DATA SERIALIZATION#
    #------------------#

    def parse_xml(self, filename):
        """Calls the motorGroup load routine"""

        parsed = self.motorGroup.load(filename)

        if not parsed:
            self.ui.calib_default_radio.setChecked(True)
        else:
            self.ui.calib_default_radio.setChecked(False)

        self.ui.calib_ml_per_rad_line.setText(str(self.motor.mL_per_rad))
        self.ui.calib_pos_per_rad_line.setText(str(self.motor.motor_position_per_rad))

        
    def write_xml(self,filename):
        """Calls the motorGroup serialize routine"""
        #call
        self.motorGroup.serialize(filename)

        #update calibration display data
        self.ui.calib_default_radio.setChecked(False)
        self.ui.calib_ml_per_rad_line.setText(str(self.motor.mL_per_rad))
        self.ui.calib_pos_per_rad_line.setText(str(self.motor.motor_position_per_rad))

    def populate_xml(self):
        """checks the current directory for xml files and adds 
            the paths."""

        for i in range(self.ui.xml_select.count()):
            self.ui.xml_select.removeItem(i)

        #thanks to: http://stackoverflow.com/a/3207973/782170
        for(path, names, fnames) in os.walk('.'):
            for n in fnames:
                d=path+n
                end=d[-4:]
                if end.lower()=='.xml':
                    
                    self.ui.xml_select.addItem("")
                    self.ui.xml_select.setItemText(self.ui.xml_select.count()-1, QtCore.QCoreApplication.translate("MainWindow", d))

    #--------------------#
    #CHANGE PUMP SETTINGS#
    #--------------------#

    def switch_pump(self):
        """Switches which pump is currently being used."""
        text=str(self.ui.pump_select.currentText())
        num=text[-1:]
        sym=syringe_motor.convertToSymbol(num)
        
        try:
            self.motor=self.motorGroup.motordict[num]
            self.ui.pump_exists.setText("Exists. In use.")
            #self.motor.connect(self.ui.port_select.currentText(),self.motor.srl_port.baudrate,self.motor.motor_address)
        except KeyError:
            self.ui.console.appendPlainText("err: motor does not exist")
                   
        
        
        self.motorGroup.serialize('syringe_pump_data.xml') 

    def new_pump(self):
        """Creates a new pump."""

        text=str(self.ui.pump_select.currentText())
        num=text[-1:]
        sym=syringe_motor.convertToSymbol(num)

        if self.motorGroup.motordict.get(num, None)==None:
            self.motorGroup.motordict[num]=syringe_motor.Motor()
            self.motorGroup.motordict[num].motor_address=sym
            self.ui.pump_exists.setText("Exists.")
        else:
            self.ui.console.appendPlainText("err: motor already exists")
        
        self.motorGroup.serialize('syringe_pump_data.xml') 
   
    def delete_pump(self):
        "Deletes an existing pump."

        text=str(self.ui.pump_select.currentText())
        num=text[-1:]
        sym=syringe_motor.convertToSymbol(num)

        if self.motorGroup.motordict.get(num,None)!=None:
            if self.motorGroup.motordict[num]==self.motor:
                del self.motor
            del self.motorGroup.motordict[num]
            self.ui.pump_exists.setText("Does Not Exist.")
            #gc.collect()
        else:
            self.ui.console.appendPlainText("err: Motor does not exist")

        self.motorGroup.serialize('syringe_pump_data.xml') 


    def select_pump(self, text):
        """Selects which pump the class will be outputting to.
        
        Args:
            text: text from the dropdown menu with all possible motor names.

        """
        num=text[-1:]
        
        #try:
        #    print(self.motorGroup.motordict[num])
        #except KeyError:
        #    print("KE")

        try:
            if self.motorGroup.motordict.get(num,None)==None:
                self.ui.pump_exists.setText("Does Not Exist.")
            elif self.motorGroup.motordict[num]==self.motor:
                self.ui.pump_exists.setText("Exists. In Use.")
            else:
                self.ui.pump_exists.setText("Exists.")
        except AttributeError:
            #This only ever occurs when self.motor was deleted.
            # In that case, the motordict returned a motor, and
            # it can't be self.motor, because that doen't exist.
            self.ui.pump_exists.setText("Exists.")

    def no_max(self):
        """Sets the motor value to somewhere near the middle of possible motor.motor_positions."""
        if self.motor.is_max_set:
            self.motor.motor_position=1073741824+self.motor.motor_position
            self.motor.sendRawCommand("/"+self.motor.motor_address+"z"+str(self.motor.motor_position)+"R")
            self.motor.max_pos=1073741824+self.motor.max_pos
            self.ui.no_max_button.setChecked(True)
            self.ui.set_max_button.setChecked(False)
            self.motor.is_max_set=False
            self.ui.set_min_button.setChecked(self.motor.is_min_set)
            self.ui.no_min_button.setChecked(not self.motor.is_min_set)

            self.show_max_draw()
            self.show_max_inject()

    def set_max(self):
        """Sets the current position to the maximum cc."""
        if not self.motor.is_max_set:
            self.motor.max_pos=abs(self.motor.max_pos-self.motor.motor_position)
            self.motor.motor_position=0
            self.motor.sendRawCommand("/"+self.motor.motor_address+"z0R")
            self.ui.set_max_button.setChecked(True)
            self.ui.no_max_button.setChecked(False)
            self.motor.is_max_set=True
            self.ui.set_min_button.setChecked(self.motor.is_min_set)
            self.ui.no_min_button.setChecked(not self.motor.is_min_set)

            self.show_max_draw()
            self.show_max_inject()

    def set_min(self):
        """Sets the current position to the minimum cc."""
        if not self.motor.is_min_set:
            self.motor.max_pos=self.getPosition()
            self.ui.set_min_button.setChecked(True)
            self.ui.no_min_button.setChecked(False)
            self.motor.is_min_set=True
            self.ui.set_max_button.setChecked(self.motor.is_max_set)
            self.ui.no_max_button.setChecked(not self.motor.is_max_set)

            self.show_max_draw()
            self.show_max_inject()

    def no_min(self):
        """Sets the max position to a high value that you'll never reach."""
        if self.motor.is_min_set:
            self.motor.max_pos=2147483647#(2^31)-1
            self.ui.no_min_button.setChecked(True)
            self.ui.set_min_button.setChecked(False)
            self.motor.is_min_set=False
            self.ui.set_max_button.setChecked(self.motor.is_max_set)
            self.ui.no_max_button.setChecked(not self.motor.is_max_set)

            self.show_max_draw()
            self.show_max_inject()
  
    #--------------------------#
    #MOTOR CONNECTION FUNCTIONS#
    #--------------------------#

    def scan_ports(self):
        for p in syringe_motor.scan_ports():
            self.ui.port_select.addItem(p)

    def select_port(self, string):
        self.motor.select_port=serial.Serial(string)
        self.motor.connect(string,self.motor.srl_port.baudrate,self.motor.motor_address)
        self.ui.console.appendPlainText("Port changed. Pleas initialize.")

    def select_baud(self, text):
        self.motor.srl_port.baudrate=int(text)
        
        self.ui.console.appendPlainText("Baud changed. Please initialize.")
   #-------------------------#
   #IMPORTANT MOTOR FUNCTIONS#
   #-------------------------#

    def checkVelocity(self):
        """Checks and reports if the motor is running at the correct velocity.
        
        Note:
            This function may not be useful for motors with no encoder wheels.
        Depricated:
            Too quick to be accurate.
            Needs to be implemented using a callback to be accurate.
        
        """
        pos1txt=self.motor.sendRawCommand("/"+self.motor.motor_address+"?0")
        t1=time.clock()
        pos2txt=self.motor.sendRawCommand("/"+self.motor.motor_address+"?0")
        t2=time.clock()

        p1=[int(s) for s in pos1txt.split('\x00') if s.isdigit()]
        p2=[int(s) for s in pos2txt.split('\x00') if s.isdigit()]

        #print(pos1txt)
        #print(pos2txt)
        #print(t1)
        #print(t2)
        #print(p1[0])
        #print(p2[0])

        vMeasured=(p2[0]-p1[0])/(t2-t1)#measure velocity in microsteps / sec

        vReptxt=self.motor.sendRawCommand("/"+self.motor.motor_address+"?2")

        #print(vReptxt)

        vRep=[int(s) for s in vReptxt.split('\x00') if s.isdigit()]
        vReported=vRep[0]*32

        #print(vRep)
        #print(vReported)

        if vMeasured>0:
            direction="injecting"
        else:
            direction="drawing"

        #check if velocity is withing 5% of reuested
        if vMeasured==0:
            self.ui.console.appendPlainText("motor is not moving.")
        elif (abs(vMeasured)-vReported) < 0.05*vReported:
            percent=100*((abs(vMeasured)-vReported)/vReported)
            self.ui.console.appendPlainText("motor is moving.")
            #self.ui.console.appendPlainText("Motor is safely "+direction+" within "+str(percent)+"% of requested velocity (R:"+str(vReported)+",M:"+str(vMeasured)+")")
        else:
            percent=100*((abs(vMeasured)-vReported)/vReported)
            self.ui.console.appendPlainText("motor is moving.")
            #self.ui.console.appendPlainText("Motor is unsafely "+direction+" "+str(percent)+"% off from requested velocity (R:"+str(vReported)+",M:"+str(vMeasured)+")")
            #self.ui.console.appendPlainText("Please check again in case this query was run during a start or stop operation.")
        
    def checkStatus(self):
        """Checks if the motor is working"""
        motor_name=self.motor.sendRawCommand("/"+self.motor.motor_address+"&")

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
        txt=self.motor.sendRawCommand("/"+self.motor.motor_address+"?0")
        #print(str(txt))
        n=[int(s) for s in txt.split('\x00') if s.isdigit()]
        #print(n)

        return int(n[0])

    def stop(self):
        """Stops the motor."""
        self.motor.sendRawCommand("/"+self.motor.motor_address+"TR")
        self.motor.motor_position=self.getPosition()

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
        top_wait_time=float(self.ui.pumping_top_wait_time_num.text())*1000
        push_time=float(self.ui.pumping_push_time_num.text())
        bottom_wait_time=float(self.ui.pumping_bottom_wait_time_num.text())*1000
        
        #check info
        if self.vol<0 or no_pumps<0 or pull_time<0 or top_wait_time<0 or push_time<0 or bottom_wait_time<0:
            self.ui.console.appendPlainText("err: negative values not allowed.")
            return

           
        self.motor.rad = self.vol/self.motor.mL_per_rad
        pos1=self.motor.motor_position
        pos2=self.motor.motor_position-self.motor.rad*self.motor.motor_position_per_rad

        #check info again...
        if pos2<0:
            self.ui.console.appendPlainText("warn: could not go past 0 position. Volume will not be as specified!")
            pos2=0

        #Impossible. Pumping cycle always starts by drawing.
        #if pos1>self.max_pos:
        #    self.ui.console.appendPlainTest("Warn: could not go past max position. Volume will not be as specififed!")

        pull_vel=abs((self.motor.rad*self.motor.motor_position_per_rad)/pull_time)
        push_vel=abs((self.motor.rad*self.motor.motor_position_per_rad)/push_time)

        if pull_vel>732143 or push_vel>732143:
            self.ui.console.appendPlainText("err: motor is not accurate at high speeds.")
            return
        
        large_note=False
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
            large_note=True
        else:
            top_wait_string="M"+str(int(top_wait_time))
        if bottom_wait_time>30000:
            bottom_wait_string="gM30000"
            bdiv=bottom_wait_time//30000
            bottom_wait_string+="G"+str(int(bdiv))
            bmod=bottom_wait_time%30000
            bottom_wait_string+="M"+str(int(bmod))
            large_note=True
        else:
            bottom_wait_string="M"+str(int(bottom_wait_time))

        #Send!
        exe="/"+self.motor.motor_address+"gV"+str(int(pull_vel))+"A"+str(int(pos2))+top_wait_string+"V"+str(int(push_vel))+"A"+str(int(pos1))+bottom_wait_string+"G"+str(int(no_pumps))+"R"
        print(exe)
        self.motor.sendRawCommand(exe)

        self.show_max_draw()
        self.show_max_inject()
        
        if large_note:
            self.ui.console.appendPlainText("Note: You've selected large wait times, which the stop operation seems to have trouble with. If you are unable to send other commands after stopping a pumping operation, try turning the pump motor off and on.")

    def handleInject(self):
        """Tells the motor to inject."""

        #get and convert user input
        #Honestly, I think I added too many units
        self.motor.vol = float(self.ui.inject_amount_num.text())
        time=float(self.ui.inject_time_num.text())
        
        self.motor.rad = self.motor.vol/self.motor.mL_per_rad
        vel=(abs(self.motor.rad*self.motor.motor_position_per_rad)/time)

        #check user input
        if vel>732143:
            self.ui.console.appendPlainText("err: motor is not accurate at high speeds.")
            return
        
        #set velocity
        self.motor.sendRawCommand("/"+self.motor.motor_address+"V"+str(int(vel))+"R")
        self.motor.motor_position=self.getPosition()+self.motor.rad*self.motor.motor_position_per_rad
        #more checking...
        if self.motor.motor_position <0:
            self.ui.console.appendPlainText("warn: could not go past 0 position.")
            self.motor.motor_position=0
        if self.motor.motor_position>self.motor.max_pos:
            self.ui.console.appendPlainText("Warn: could not go past max position. Will not inject correct volume!")
            self.motor.motor_position=self.motor.max_pos

        #Inject!
        self.motor.sendRawCommand("/"+self.motor.motor_address+"A"+str(int(self.motor.motor_position))+"R")

        self.show_max_draw()
        self.show_max_inject()

    def handleCalib(self):
        """Resets the motor constants.""" 

        if self.ui.cal_expect_unit.currentText()=="mL":
            rad=float(self.ui.cal_expected_line.text())/self.motor.mL_per_rad
            actVol=float(self.ui.cal_result_line.text())
            self.motor.mL_per_rad=actVol/rad

        elif self.ui.cal_expect_unit.currentText()=="Rotations":
            expRad = float(self.ui.cal_expected_line.text())*2*math.pi
            actRad = float(self.ui.cal_result_line.text())*2*math.pi
            mpos = expRad*self.motor.motor_position_per_rad
            self.motor.motor_position_per_rad=mpos/actRad

        elif self.ui.cal_expect_unit.currentText()=="Radians":
            expRad = float(self.ui.cal_expected_line.text())
            actRad = float(self.ui.cal_result_line.text())
            mpos = expRad*self.motor.motor_position_per_rad
            self.motor.motor_position_per_rad=mpos/actRad

        elif self.ui.cal_expect_unit.currentText()=="Degrees":
            expRad = float(self.ui.cal_expected_line.text())*(math.pi/180)
            actRad = float(self.ui.cal_result_line.text())*(math.pi/180)
            mpos = expRad*self.motor.motor_position_per_rad
            self.motor.motor_position_per_rad=mpos/actRad

        self.write_xml('syringe_pump_data.xml')
        self.show_max_draw()
        self.show_max_inject()

if __name__ == '__main__':
    import sys
    
    app = QApplication(sys.argv)
    
    wind = ControllerWindow()
    
#    input= wind.read
#    sys.stdout = wind
    
    wind.show()
    
    sys.exit(app.exec_())
    
    
