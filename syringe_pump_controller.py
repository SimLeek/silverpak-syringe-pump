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
    
        self.ui.calibrate_pump_button.clicked.connect(self.handleInject)

        self.mL_per_rad=0.01/(2*math.pi)
        self.pos_per_rad=100000/(2*math.pi)

        self.pos=0

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
        self.ui.console.appendPlainText("Motor initialized.")

        self.position=self.motor.position()
    

    def handleInject(self):
        if self.ui.cal_by_vol_radio.isChecked():
            vol = float(self.ui.cal_by_vol_num.text())
            if str(self.ui.cal_by_vol_unit.currentText()) == "mL":
                pass
            rad = vol/self.mL_per_rad
        else:#by rotations
            rad = float(self.ui.cal_by_rot_num.text())
            if str(self.ui.cal_by_rot_unit.currentText()) == u"°":
                rad = rad*(math.pi/180.)
            elif str(self.ui.cal_by_rot_unit.currentText()) == "θ":
                pass
            elif str(self.ui.cal_by_rot_unit.currentText()) == "no. rev.":
                rad= rad*(2*math.pi)
        print(self.motor.position(),rad*self.pos_per_rad)
        self.pos=self.pos+rad*self.pos_per_rad
        if self.pos <0:
            self.pos=0
        print(self.pos)
        self.motor.sendRawCommand("/1A"+str(int(self.pos))+"R")
        print("/1A"+str(int(self.pos))+"R")

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
	
	
