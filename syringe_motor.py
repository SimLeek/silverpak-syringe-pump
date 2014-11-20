#vim: set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab:
import threading
import serial
import time
import os
import xml.etree.ElementTree as ET
import fnmatch
def scan_ports():
    portNames= []
    if os.name == 'posix' or os.name == 'mac':
        for filename in os.listdir('/dev/'):
            if fnmatch.fnmatch(filename, 'cu.usbserial*') or fnmatch.fnmatch(filename, 'tty[!0123456789]*') or fnmatch.fnmatch(filename, 'COM*'):
                portNames.append('/dev/' + filename)
    else:
        portNames = ["COM%i" % i for i in range(1, 10)]

    return portNames 

def convertToNum(sym):
    if sym=='@':
        return '0'
    elif sym=='1':
        return '1'
    elif sym=='2':
        return '2'
    elif sym=='3':
        return '3'
    elif sym=='4':
        return '4'
    elif sym=='5':
        return '5'
    elif sym=='6':
        return '6'
    elif sym=='7':
        return '7'
    elif sym=='8':
        return '8'
    elif sym=='9':
        return '9'
    elif sym==':':
        return 'A'
    elif sym==';':
        return 'B'
    elif sym=='<':
        return 'C'
    elif sym=='=':
        return 'D'
    elif sym=='>':
        return 'E'
    elif sym=='?':
        return 'F' 


def convertToSymbol(num):
    if num=='0':
        return '@'
    elif num=='1':
        return '1'
    elif num=='2':
        return '2'
    elif num=='3':
        return '3'
    elif num=='4':
        return '4'
    elif num=='5':
        return '5'
    elif num=='6':
        return '6'
    elif num=='7':
        return '7'
    elif num=='8':
        return '8'
    elif num=='9':
        return '9'
    elif num=='A':
        return ':'
    elif num=='B':
        return ';'
    elif num=='C':
        return '<'
    elif num=='D':
        return '='
    elif num=='E':
        return '>'
    elif num=='F':
        return '?' 

class MotorGroup:
    def __init__(self):
        self.motordict={}    

    def serialize(self, filename):
        #make xml
        root=ET.Element('constants')
        for name, motorClass in self.motordict.items():
                motorElement=ET.SubElement(root, 'motor_'+name)
                mL_per_rad=ET.SubElement(motorElement, 'mL_per_rad')
                mL_per_rad.text=str(motorClass.mL_per_rad)
                pos_per_rad=ET.SubElement(motorElement, 'pos_per_rad')
                pos_per_rad.text=str(motorClass.motor_position_per_rad)
                motor_pos=ET.SubElement(motorElement, 'motor_pos')
                motor_pos.text=str(motorClass.motor_position)
                max_pos=ET.SubElement(motorElement, 'max_pos')
                max_pos.text=str(motorClass.max_pos)

        #write xml
        tree=ET.ElementTree(root)
        tree.write(filename)
 
    def load(self, filename):
        """Gets serialized data that may change between motors.

        Args:
            filename (str): name of the xml file to parse

        Raises:
            ValueError, ParseError

        TODO: serialize entire motordict, not just the current motor!

        """

        xml_good=True
        
        self.motordict.clear()


        #scan doc
        try:
            tree=ET.parse(filename)
            root=tree.getroot()

            for m in root:
                p=m.tag.lower()
                num=p[-1:]
                #check that pump tag ends with a valid number (STOP HERE)
                if (ord(num)>=ord('0') and ord(num)<=ord('9')) or (ord(num)>=ord('a') and ord(num)<=ord('f')):
                        self.motordict[num]=Motor()
                        self.motordict[num].motor_address=convertToSymbol(num)
                else:
                    continue
                for child in m:
                    if child.tag=='mL_per_rad':
                        self.motordict[num].mL_per_rad=float(child.text)
                    elif child.tag=='pos_per_rad':
                        self.motordict[num].motor_position_per_rad=float(child.text)
                    elif child.tag=='motor_pos':
                        self.motordict[num].motor_position=float(child.text)
                    elif child.tag=='max_pos':
                        self.motordict[num].max_pos=float(child.text)
                
                #check data
                if not hasattr(self,'mL_per_rad'):
                    self.motordict[num].mL_per_rad=0.016631691553103064#found experimentally
                    xml_good=False
                if not hasattr(self,'pos_per_rad'):
                    self.motordict[num].motor_position_per_rad=8156.69083345965#found experimentally(on free motor)
                    xml_good=False

                if not hasattr(self, 'motor_pos'):
                    xml_good=False

                if not hasattr(self, 'max_pos'):
                    xml_good=False
         

        except EnvironmentError:
            pass

        
        #fix doc
        if not xml_good: 
            self.serialize(filename)

        return xml_good


class Motor:
    """"""

    def __init__(self):
        """Creates all the variables needed for the class funcionts
        
        Also creates default variables used by the calling class.
        """
        self.srl_rlock=threading.RLock()
        self.srl_port=serial.Serial()
        self.srl_port.bytesize=8
        self.srl_port.parity=serial.PARITY_NONE
        self.srl_port.stopbits=serial.STOPBITS_ONE
        self.srl_port.baudrate=9600

        self._nextsleep=time.time()

        self.motor_address='1'
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

    def connect(self,port,baud=9600,motor_address='1'):
        """"""
        with self.srl_rlock:
            
            self.srl_port.port=port
            self.srl_port.baudrate=baud
            self.srl_port.timeout=0.02 
            self.srl_port.open()
            response = self.sendRawCommand("/"+motor_address+"Q")
            print('/'+motor_address+"Q")
            print(response)
            if response != None:
                self.motor_address=motor_address
                return True

            
                pass
            self.disconnect()
            return False

    def disconnect(self):
        """"""
        with self.srl_rlock:
            if self.srl_port.isOpen():
                self.srl_port.close()
    
    def wait(self, delay):
        """wait for the serial port to do things before you use it."""
        time.sleep(max(0,self._nextsleep - time.time()))
        self._nextsleep=time.time() + delay

    def sendRawCommand(self, message, delay=None):
        """"""
        if delay==None:
            delay=2*(float(self.srl_port.bytesize)/self.srl_port.baudrate)

        with self.srl_rlock:
            if not self.srl_port.isOpen(): 
                raise serial.serialutil.SerialException("port not open")
            
            self.wait(delay)
            try:
                garbage = self.srl_port.read()
            except:
                garbage = None

            self.wait(delay)
            #try:
            self.srl_port.write(bytes((message+"\r").encode("utf-8")))
            #except Exception as ex:
            #    import traceback
            #    traceback.print_exception(type(ex), ex, ex.__traceback__)
            
            totalRx=""
            responseContent=None

            while True:
                self.wait(delay)
                try:
                    rxStr=self.srl_port.read()
                    if rxStr==b'\xff':
                        rxStr=b'f'
                    rxStr=rxStr.decode('utf-8')
                except:
                    rxStr=""

                if rxStr == "":
                    #nothing more to read
                    return responseContent

                totalRx+=rxStr

                #check completeness
                if (totalRx.find('\x03')==-1 or totalRx.find("/0")==-1):
                    continue #keep accumulating

                startTrim = totalRx.find("/0")
                trimOne = totalRx[startTrim + len("/0"):]
                finalTrim = trimOne[:trimOne.find("\x03")]
                
                responseContent = finalTrim[1:]
                totalRx=""









                


