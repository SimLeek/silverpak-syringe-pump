
Imports System.IO.Ports
Imports System.Threading
Imports System.ComponentModel

# Public classes
class SilverpakManager
    """Provides an interface to a Lin Engineering Silverpak23CE stepper motor"""

    # Public Fields
    DefaultAcceleration = 500
    DefaultBaudRate = -1
    DefaultDriverAddress As DriverAddresses = DriverAddresses.Unknown
    DefaultEncoderRatio = 10266
    DefaultHoldingCurrent = 5
    DefaultHomePolarity = 0
    DefaultMaxPosition = 500000
    DefaultMotorPolarity = 1
    DefaultPortname As String = ""
    DefaultPositionCorrectionRetries = 5
    DefaultPositionCorrectionTolerance = 5
    DefaultPositionUpdaterInterval = 200
    DefaultRunningCurrent = 50
    DefaultVelocity = 230000

    def IsActive(self):
        """Returns a value indicating whether this SilverpakManager is actively connected to a Silverpak23CE"""
        SyncLock m_motor_lock:
            return m_motorState_motor != MotorStates.Disconnected
    def IsReady(self):
        """Returns a value indicating whether the motor is ready to accept a command (i.e. connected, initialized, and stopped)"""
        SyncLock m_motor_lock:
            return m_motorState_motor = MotorStates.Ready
    def position(self):
        return _position

    # Public Events TODO
    # Raised when the connection to the Silverpak23CE is lost.
    #Public Event ConnectionLost As EventHandler
    # Raised when the motor stops moving.
    #Public Event StoppedMoving As EventHandler(Of StoppedMovingEventArgs)
    # Raised when the motor's position changes. Read the Position property to get the position.
    #Public Event PositionChanged As EventHandler

    def __init__(self):
        _connectionManager_motor = SilverpakConnectionManager(m_components)
        m_acceleration As Integer = DefaultAcceleration
        m_baudRate As Integer = DefaultBaudRate
        m_driverAddress As DriverAddresses = DefaultDriverAddress
        m_encoderRatio As Integer = DefaultEncoderRatio
        m_holdingCurrent As Integer = DefaultHoldingCurrent
        m_homePolarity As Integer = DefaultHomePolarity
        m_maxPosition As Integer = DefaultMaxPosition
        m_motorPolarity As Integer = DefaultMotorPolarity
        m_portName As String = DefaultPortname
        m_positionCorrectionRetries As Integer = DefaultPositionCorrectionRetries
        m_positionCorrectionTolerance As Integer = DefaultPositionCorrectionTolerance
        m_positionUpdaterInterval As Integer = DefaultPositionUpdaterInterval
        m_runningCurrent As Integer = DefaultRunningCurrent
        m_velocity As Integer = DefaultVelocity
        m_position As Integer = 0
        
        # Fields in the SyncLock group: motor
        # Lock object for the SyncLock group: motor.
        m_motor_lock As Object
        # Connection manager component. Part of the SyncLock group: motor.
        m_connectionManager_motor As SilverpakConnectionManager
        # The present state of the motor. Part of the SyncLock group: motor.
        m_motorState_motor As MotorStates = MotorStates.Disconnected
        
        # Fields in the SyncLock group: posUpd
        # Lock object for the SyncLock group: posUpd.
        m_posUpd_lock As Object 'SyncLock object for this group
        # Used to cancel the position updater thread. Part of the SyncLock group: posUpd.
        m_keepPositionUpdaterRunning_posUpd As Boolean
        # Thread that periodically gets the position of the motor. Part of the SyncLock group: posUpd.
        m_positionUpdaterThread_posUpd As Thread(AddressOf positionUpdater_run)



    # Public methods
    def Connect(self):
        """
        Attempts to connect to a Silverpak23CE. 
        The PortName, BaudRate, and DriverAddress properties must be set or an ArgumentException will be thrown. 
        To auto-detect these properties, see FindAndConnect(). 
        The IsActive property must return False when calling this method or an InvalidSilverpakOperationException will be thrown.
        """
        SyncLock m_motor_lock:
            # Validate state and connection properties
            if m_motorState_motor != MotorStates.Disconnected: raise InvalidSilverpakOperationException("Connection is already active. Make sure the IsActive property returns False before calling this method.")
            if m_portName == DefaultPortname: raise ArgumentException("PortName property must be set before calling this method. See also FindAndConnect().")
            if m_baudRate == DefaultBaudRate: raise ArgumentException("BaudRate property must be set before calling this method. See also FindAndConnect().")
            if m_driverAddress == DefaultDriverAddress: raise ArgumentException("DriverAddress property must be set before calling this method. See also FindAndConnect().")

            # Initialize connection manager's properties
            m_connectionManager_motor.PortName = m_portName
            m_connectionManager_motor.BaudRate = m_baudRate
            m_connectionManager_motor.DriverAddress = m_driverAddress
            # Attempt to connect
            if m_connectionManager_motor.Connect():
                # Connection succeeded
                m_motorState_motor = MotorStates.Connected
                return True
            Else
                # Connection failed
                return False

    def FindAndConnect(self):
        """
        Attempts to find and connect to a Silverpak23CE. 
        if any of the properties PortName, BaudRate, and DriverAddress are set to their defaults, all of their possible values will be searched. 
        After a successful connection, these properties will be set to their discovered values. 
        The IsActive property must return False when calling this method or an InvalidSilverpakOperationException will be thrown.
        """
        SyncLock m_motor_lock:
            # Validate state
            if m_motorState_motor != MotorStates.Disconnected: raise InvalidSilverpakOperationException("Connection is already active. Make sure the IsActive property returns False before calling this method.")

            # Get information for all COM ports being searched
            Dim portInfos() As PortInformation = SearchComPorts(m_portName, m_baudRate, m_driverAddress)
            # Search the list of information for an available Silverpak23CE
            for iPI in portInfos:
                if iPI.PortStatus = PortStatuses.AvailableSilverpak:
                    # Listed available Silverpak23CE found
                    # Initialize connection manager's properties
                    m_connectionManager_motor.PortName = iPI.PortName
                    m_connectionManager_motor.BaudRate = iPI.BaudRate
                    m_connectionManager_motor.DriverAddress = iPI.DriverAddress
                    # Attempt to connect
                    # This should only evaluate to Flase in the event that the Silverpak23CE was disconnected between the call to SearchComPorts and now
                    if m_connectionManager_motor.Connect(): 
                        # Connection succeeded
                        # Save connection properties
                        m_portName = iPI.PortName
                        m_baudRate = iPI.BaudRate
                        m_driverAddress = iPI.DriverAddress
                        m_motorState_motor = MotorStates.Connected
                        return True
                    # In the rare occasion that block is skipped, try: the next iPI
            # End of list was reached and no available Silverpak23CE was found
            return False

    def InitializeMotorSettings(self):
        """
        Initialization Step 1. 
        This method will set the motor settings as specified by this SilverpakManager's properties.
        This method does not cause the motor to move.
        The next step is InitializeSmoothMotion().
        Calling this method out of order will raise an InvalidSilverpakOperationException.
        """
        SyncLock m_motor_lock:
            # Validate state
            if m_motorState_motor != MotorStates.Connected: raise InvalidSilverpakOperationException("Initialization methods must be called in the proper order.")

            # Send settings-initialization command
            m_connectionManager_motor.Write(GenerateMessage(m_driverAddress, generateFullInitCommandList()), 4.0)
            # Update state
            m_motorState_motor = MotorStates.InitializedSettings
    
    def ResendMotorSettings(self):
        """
        Call this method if any changes to the motor settings properties need to be applied.
        This method does not cause the motor to move.
        Calling this method will raise an InvalidSilverpakOperationException if the IsActive property returns False or if the motor is moving.
        """
        SyncLock m_motor_lock:
            # Validate state
            if m_motorState_motor == MotorStates.Disconnected: raise InvalidSilverpakOperationException("Connection is not active.")
            if m_motorState_motor in (
                    MotorStates.InitializingCoordinates_moveToZero,
                    MotorStates.InitializingCoordinates_calibrateHome,
                    MotorStates.Moving
                )
                raise InvalidSilverpakOperationException("Cannot resend motor settings while the motor is moving.")
            # Send settings command
            m_connectionManager_motor.Write(GenerateMessage(m_driverAddress, generateResendInitCommandList()), 4.0)

    def InitializeSmoothMotion(self):
        """
        Initialization Step 2. 
        This method will send a small motion command five times to bypass any initialization quirks that some motors are prone to exhibit.
        This method causes the motor to move up to 5 microsteps in the positive direction and causes the motor to briefly produce a rapid tapping sound.
        The next step is InitializeCoordinates().
        Calling this method out of order will raise an InvalidSilverpakOperationException.
        """
        SyncLock m_motor_lock:
            # Validate state
            if m_motorState_motor != MotorStates.InitializedSettings: raise InvalidSilverpakOperationException("Initialization methods must be called in the proper order.")
            
            # Send a small motion command five times
            smoothMotionInitMsg = GenerateMessage(m_driverAddress, GenerateCommand(Commands.GoPositive, "1"))
            for i in range(5):
                m_connectionManager_motor.Write(smoothMotionInitMsg, 3.0!)
            # Update state
            m_motorState_motor = MotorStates.InitializedSmoothMotion
    
    def InitializeCoordinates(self):
        """
        Initialization Step 3. 
        This method will send the motor looking for its upper limit switch so it can zero its coordinate system.
        This method causes the motor to move in the negative direction until it trips the upper limit switch.
        The next initialization step is to wait for the CoordinatesInitialized event or to wait for the IsReady property to return True.
        Calling this method out of order will raise an InvalidSilverpakOperationException.
        """
        SyncLock m_motor_lock:
            # Validate state
            if m_motorState_motor != MotorStates.InitializedSmoothMotion: raise InvalidSilverpakOperationException("Initialization methods must be called in the proper order.")

            moveToZero()
        # Now that the motor is moving, begin listening for position changes
        startPositionUpdater()
    
    def moveToZero(self):
        # move to zero in preparation for home calibration
        cmd = GenerateCommand(Commands.SetPosition, int(m_maxPosition * (m_encoderRatio / 1000.0)))
        cmd += GenerateCommand(Commands.SetEncoderRatio, m_encoderRatio)
        cmd += GenerateCommand(Commands.GoAbsolute, 0)
        message = GenerateMessage(m_driverAddress, cmd)
        m_connectionManager_motor.Write(message, 2.0)

        # Update state
        m_motorState_motor = MotorStates.InitializingCoordinates_moveToZero

    def GoInfinite(self, positive):
        """
        Sends the motor either to position 0 or to the position specified by the MaxPosition property.
        Calling this method before the motor has been fully initialized will raise an InvalidSilverpakOperationException.
        """
        GoToPosition({True: m_maxPosition, False: 0}[positive])

    def StopMotor(self):
        """
        Stops the motor.
        Calling this method when the IsActive property returns False will raise an InvalidSilverpakOperationException.
        """
        SyncLock m_motor_lock:
            # Validate state
            if m_motorState_motor = MotorStates.Disconnected: raise InvalidSilverpakOperationException("Connection is not active.")

            # Send stop command
            Static s_stopMessage As String = GenerateMessage(m_driverAddress, GenerateCommand(Commands.TerminateCommand))
            m_connectionManager_motor.Write(s_stopMessage, 1.0!)
            # Update state if applicable
            if m_motorState_motor in (
                    MotorStates.InitializingCoordinates_moveToZero,
                    MotorStates.InitializingCoordinates_calibrateHome,
                ):
                m_motorState_motor = MotorStates.AbortingCoordinateInitialization
    
    def GoToPosition(self, position):
        """
        Sends the motor to the passed position.
        Calling this method before the motor has been fully initialized will raise an InvalidSilverpakOperationException.
        """
        SyncLock m_motor_lock:
            # Validate state
            if m_motorState_motor not in (
                    MotorStates.Ready,
                    MotorStates.Moving,
                ):
                raise InvalidSilverpakOperationException("Motor is not fully initialized")
            # Send absolute motion command
            m_connectionManager_motor.Write(GenerateMessage(m_driverAddress, GenerateCommand(Commands.GoAbsolute, position)), 1.0)
            # Update state
            m_motorState_motor = MotorStates.Moving
    
    def Disconnect(self):
        """
        Terminates the connection to the Silverpak23CE and closes the COM port.
        Calling this method will raise an InvalidSilverpakOperationException if the IsActive property returns False or if the motor is moving.
        """
        SyncLock m_motor_lock:
            # Validate state
            if m_motorState_motor == MotorStates.Disconnected: raise InvalidSilverpakOperationException("Connection is not active.")
            if m_motorState_motor in (
                    MotorStates.InitializingCoordinates_moveToZero,
                    MotorStates.InitializingCoordinates_calibrateHome,
                    MotorStates.Moving,
                ):
                raise InvalidSilverpakOperationException("Disconnecting while the motor is moving is not allowed.")

            # Disconnect
            m_connectionManager_motor.Disconnect()
            # Update state
            m_motorState_motor = MotorStates.Disconnected
    
    s_errorCallback = None
    
    # Event raisers
    def OnConnectionLost(self):
        RaiseEvent ConnectionLost(self, EventArgs)
    # Method that raises the event CoordinatesInitializationAborted.
    def OnCoordinatesInitializationAborted(self):
        RaiseEvent StoppedMoving(self, StoppedMovingEventArgs(StoppedMovingReason.InitializationAborted))
    # Method that raises the event CoordinatesInitialized.
    def OnCoordinatesInitialized(self):
        RaiseEvent StoppedMoving(self, StoppedMovingEventArgs(StoppedMovingReason.Initialized))
    # Method that raises the event PositionChanged.
    def OnPositionChanged(self):
        RaiseEvent PositionChanged(self, EventArgs)
    # Method that raises the event StoppedMoving.
    def OnStoppedMoving(self):
        RaiseEvent StoppedMoving(self, StoppedMovingEventArgs(StoppedMovingReason.Normal))
    
    # Private methods
    def __exit__(self):
        """Disposes this component."""
        if m_components  Nothing:
            m_components.Dispose()
            stopPositionUpdater()
    def Dispose(self):
        self.__exit__()
    
    # Makes sure the position updater thread is running.
    def startPositionUpdater(self):
        SyncLock m_posUpd_lock:
            m_keepPositionUpdaterRunning_posUpd = True # make sure the position updater thread doesn't cancel
            if not m_positionUpdaterThread_posUpd.IsAlive: # only activate it when it's not active
                if m_positionUpdaterThread_posUpd.ThreadState == ThreadState.Stopped: # if it's previously completed running
                    m_positionUpdaterThread_posUpd = Thread(AddressOf positionUpdater_run) # reinstantiate the thread
                m_positionUpdaterThread_posUpd.Start() 'start the thread

    def stopPositionUpdater(self):
        """Stops the position updater thread and makes sure it dies."""
        if Thread.CurrentThread ==  m_positionUpdaterThread_posUpd:
            'the position updater thread cannot stop itself; a thread can never see itself die.
            Dim t As Thread(AddressOf stopPositionUpdater_not_positionUpdaterThread)
            t.Start() 'stop the position updater thread on a seperate thread
        else:
            stopPositionUpdater_not_positionUpdaterThread()
    def stopPositionUpdater_not_positionUpdaterThread(self):
        """Stops the position updater thread and makes sure it dies. This method cannot be called on the position updater thread."""
        try:
            SyncLock m_posUpd_lock:
                # cancel the position updater
                m_keepPositionUpdaterRunning_posUpd = False
                if m_positionUpdaterThread_posUpd IsNot Nothing:
                    Dim timeoutTime As Integer = Environment.TickCount + 1000
                    while m_positionUpdaterThread_posUpd.IsAlive:
                        if Environment.TickCount >= timeoutTime: break
                    # make sure the position updater thread dies before releasing the SyncLock
        except ex As Exception
            invokeErrorCallback(ex)

    def positionUpdater_run(self):
        """Method that the position getter thread runs."""
        try:
            # check for cancelation
            while m_keepPositionUpdaterRunning_posUpd:
                # Keep time according to Environment.TickCount
                nextIterationTime = Environment.TickCount + m_positionUpdaterInterval
                # Update postion
                updatePosition()
                # Wait for the next iteration time
                Thread.Sleep(Math.Max(0, nextIterationTime - Environment.TickCount))
        except ex As Exception
            invokeErrorCallback(ex)
    
    def updatePosition():
        """Updates the Position property by querying the position of the motor."""
        # store a function to call after the SyncLock has been released
        callbackAction = None
        SyncLock m_motor_lock
            Static s_getPositionCmd As String = GenerateCommand(Commands.QueryMotorPosition)
            getPositionMessage = GenerateMessage(m_driverAddress, s_getPositionCmd)
            # make sure we know whether it's been set by starting it at an unlikely value
            newPosition = Integer.MinValue
            response = None
            Static s_homeCalibrationSteps As Integer
            try:
                response = m_connectionManager_motor.WriteAndGetResponse(getPositionMessage, 1.0)
            except ex As InvalidSilverpakOperationException:
                # the SilverpakManager's been disconnected
                # shut down updater thread
                callbackAction = stopPositionUpdater
                GoTo ExitAndCallback
            # Serial Port is still active
            if response IsNot Nothing AndAlso IsNumeric(response):
                # Got a valid response
                newPosition = int(response)
            # track the number of times we didn't receive a valid response
            Static s_failCount As Integer = 0
            if m_position = newPosition:
                # motor stopped moving
                s_failCount = 0
                if m_motorState_motor == MotorStates.InitializingCoordinates_moveToZero:
                    # wait! sometimes the motor will stop at 5000000 and lie about being at the top (stupid old firmware)
                    if Math.Abs(m_position - 5000000) < 100:
                        moveToZero()
                    else:
                        m_motorState_motor = MotorStates.InitializingCoordinates_calibrateHome
                        # Send the homing message
                        initCoordMessage = GenerateMessage(m_driverAddress, GenerateCommand(Commands.GoHome, CInt(m_maxPosition * (m_encoderRatio / 1000))))
                        m_connectionManager_motor.Write(initCoordMessage, 1.0)
                        s_homeCalibrationSteps = 0
                elif m_motorState_motor == MotorStates.InitializingCoordinates_calibrateHome:
                    m_motorState_motor = MotorStates.Ready
                    callbackAction = Action(AddressOf OnCoordinatesInitialized)
                elif m_motorState_motor == MotorStates.AbortingCoordinateInitialization
                    m_motorState_motor = MotorStates.InitializedSmoothMotion
                    callbackAction = Action(AddressOf OnCoordinatesInitializationAborted)
                elif m_motorState_motor == MotorStates.Moving
                    m_motorState_motor = MotorStates.Ready
                    callbackAction = Action(AddressOf OnStoppedMoving)
            elif newPosition != Integer.MinValue:
                # motor changed position
                s_failCount = 0
                m_position = newPosition
                callbackAction = Action(AddressOf OnPositionChanged)
                # make sure the home calibration isn't sneaking away
                if m_motorState_motor = MotorStates.InitializingCoordinates_calibrateHome:
                    s_homeCalibrationSteps += 1
                    if s_homeCalibrationSteps > 5:
                        # Calling shenanigans on initialization
                        # stop the motor damnit
                        for _ in range(3):
                            Static s_stopMessage As String = GenerateMessage(m_driverAddress, GenerateCommand(Commands.TerminateCommand))
                            m_connectionManager_motor.Write(s_stopMessage, 1.0)
                        MsgBox("Motor shenanigans detected! This is a quirk resulting from using outdated motor firmware.\nPlease restart the program.", MsgBoxStyle.Critical, MsgBoxTitle)
                        sys.exit(1)
                    End if
                End if
            else:
                # failed to get a valid position
                s_failCount += 1
                if s_failCount >= 5:
                    # failed 5 times in a row. Silverpak23CE must no longer be available.
                    s_failCount = 0
                    # disconnect
                    m_motorState_motor = MotorStates.Disconnected
                    m_connectionManager_motor.Disconnect()
                    # raise LostConnection event
                    callbackAction = OnConnectionLost
#ExitAndCallback:
        # invoke callback sub if any
        if callbackAction IsNot Nothing:
            callbackAction.Invoke()
    
    def generateFullInitCommandList(self):
        """Produces a command list to initialize the motor from scratch."""
        Static s_initMotorSettingsProgramHeader As String = GenerateCommand(Commands.SetPosition, "0")
        # Position Correction + Optical Limit Switches
        Static s_initMotorSettingsProgramFooter As String = GenerateCommand(Commands.SetMode, "10")
        return s_initMotorSettingsProgramHeader + generateResendInitCommandList() + s_initMotorSettingsProgramFooter
    
    def generateResendInitCommandList(self):
        """Produces a command list to set the adjustable motor settings."""
        return GenerateCommand(Commands.SetHoldCurrent, m_holdingCurrent) + \
                GenerateCommand(Commands.SetRunningCurrent, m_runningCurrent) + \
                GenerateCommand(Commands.SetMotorPolarity, m_motorPolarity) + \
                GenerateCommand(Commands.SetHomePolarity, m_homePolarity) + \
                GenerateCommand(Commands.SetPositionCorrectionTolerance, m_positionCorrectionTolerance) + \
                GenerateCommand(Commands.SetPositionCorrectionRetries, m_positionCorrectionRetries) + \
                GenerateCommand(Commands.SetEncoderRatio, "1000") + \
                GenerateCommand(Commands.SetVelocity, m_velocity) + \
                GenerateCommand(Commands.SetAcceleration, m_acceleration) + \
                GenerateCommand(Commands.SetEncoderRatio, m_encoderRatio)

    def invokeErrorCallback(ex)
        """Invokes the ErrorCalback delegate if it has been set. Otherwise, re-throws the exception so that the program crashes."""
        if s_errorCallback != None:
            s_errorCallback.Invoke(ex)
        else:
            raise ex

#  The exception that is thrown when a method call in namespace Silverpak23CE is invalid for the object's current state. 
Public Class InvalidSilverpakOperationException
    Inherits InvalidOperationException
    Public Sub New()
        MyBase.New()
    End Sub
    Public Sub New(ByVal message As String)
        MyBase.New(message)
    End Sub
    Public Sub New(ByVal message As String, ByVal innerException As Exception)
        MyBase.New(message, innerException)
    End Sub
    Protected Sub New(ByVal info As Runtime.Serialization.SerializationInfo, ByVal context As Runtime.Serialization.StreamingContext)
        MyBase.New(info, context)
    End Sub
End Class

Represents a collection of data for reporting the status of a COM port
Public Class PortInformation
    The name of the COM port
    Public Property PortName() As String
        Get
            return m_portName
        End Get
        Set(ByVal value As String)
            m_portName = value
        End Set
    End Property
    The baud rate of the COM port
    Public Property BaudRate() As Integer
        Get
            return m_baudRate
        End Get
        Set(ByVal value As Integer)
            m_baudRate = value
        End Set
    End Property
    The status of the COM port
    Public Property PortStatus() As PortStatuses
        Get
            return m_portStatus
        End Get
        Set(ByVal value As PortStatuses)
            m_portStatus = value
        End Set
    End Property
    The driver address of the active Silverpak23CE if there is one
    Public Property DriverAddress() As DriverAddresses
        Get
            return m_driverAddress
        End Get
        Set(ByVal value As DriverAddresses)
            m_driverAddress = value
        End Set
    End Property

    # Field behind the PortName property
    Private m_portName As String
    # Field behind the BaudRate property
    Private m_baudRate As Integer
    # Field behind the PortStatu property
    Private m_portStatus As PortStatuses
    # Field behind the DriverAddress property
    Private m_driverAddress As DriverAddresses
End Class

Public Class StoppedMovingEventArgs
    Inherits EventArgs
    Private m_reason
    # The reason that the motor stopped moving.
    Public Property Reason() As StoppedMovingReason
        Get
            return m_reason
        End Get
        Set(ByVal value As StoppedMovingReason)
            m_reason = value
        End Set
    End Property

    Public Sub New(ByVal reason As StoppedMovingReason)
        m_reason = reason
    End Sub
End Class

'Public enums
Represents a driver address.
Public Enum DriverAddresses As Byte
    Unknown = 0
    Driver1 = Asc("1")
    Driver2 = Asc("2")
    Driver3 = Asc("3")
    Driver4 = Asc("4")
    Driver5 = Asc("5")
    Driver6 = Asc("6")
    Driver7 = Asc("7")
    Driver8 = Asc("8")
    Driver9 = Asc("9")
    DriverA = Asc(":")
    DriverB = Asc(";")
    DriverC = Asc("<")
    DriverD = Asc("=")
    DriverE = Asc(">")
    DriverF = Asc("?")
    Driver0 = Asc("@")
    Drivers1And2 = Asc("A")
    Drivers3And4 = Asc("C")
    Drivers5And6 = Asc("E")
    Drivers7And8 = Asc("G")
    Drivers9And10 = Asc("I")
    Drivers11And12 = Asc("K")
    Drivers13And14 = Asc("M")
    Drivers15And16 = Asc("O")
    Drivers1And2And3And4 = Asc("Q")
    Drivers5And6And7And8 = Asc("U")
    Drivers9And10And11And12 = Asc("Y")
    Drivers13And14And15And16 = Asc("]")
    AllDrivers = Asc("_")
End Enum

Represents the status of a COM port.
Public Enum PortStatuses
    Indicates that there is an active, available Silverpak on this COM port
    AvailableSilverpak
    Indicates that this COM port does not have an active Silverpak
    Empty
    Indicates that this COM port could not be read from or written to
    Invalid
    Indicates that this COM port is already open by another resource
    Busy
End Enum

Represents the reason that the motor stopped moving.
Public Enum StoppedMovingReason
    The motor stopped after a GoInfinite() or GoToPosition() command.
    Normal
    The InitializeCoordinates() command has completed without being interrupted.
    Initialized
    The InitializeCoordinates() command is aborted by calling the StopMotor() method.
    InitializationAborted
End Enum

'Friend classes
# Manages the connection to a Silverpak23CE through a serial port.
<ToolboxItem(False)> _
Friend Class SilverpakConnectionManager
    Inherits Component

    'Public fields
    # The command string for a safe query.
    Public Shared ReadOnly SafeQueryCommandStr As String = GenerateCommand(m_safeQueryCommand, m_safeQueryOperand)
    # The delay factor for a safe query.
    Public Const SafeQueryDelayFactor As Single = 3.0!
    # The minimum amount of time in milliseconds to wait for the Silverpak23CE to respond to a command.
    Public Const PortDelayUnit As Integer = 50

    'Public properties
    # The name of the COM port to connect to.
    Public Property PortName() As String
        Get
            return m_portName
        End Get
        Set(ByVal value As String)
            m_portName = value
        End Set
    End Property
    # The baud rate of the COM port to connect to.
    Public Property BaudRate() As Integer
        Get
            return m_baudRate
        End Get
        Set(ByVal value As Integer)
            m_baudRate = value
        End Set
    End Property
    # The driver address of the Silverpak23CE to connect to.
    Public Property DriverAddress() As DriverAddresses
        Get
            return m_driverAddress
        End Get
        Set(ByVal value As DriverAddresses)
            m_driverAddress = value
        End Set
    End Property

    'Public constructors
    Creates a instance of the SilverpakConnectionManager class. This overload is provided for Windows.Forms Class Composition Designer support.
    Public Sub New(ByVal container As System.ComponentModel.IContainer)
        MyClass.New()
        if container IsNot Nothing: container.Add(Me) 'Required for Windows.Forms Class Composition Designer support
    End Sub
    Creates a instance of the SilverpakConnectionManager class.
    Public Sub New()
        MyBase.New()
        components = Container()
        m_serialPortInterface_srlPort = InitializeSerialPort(SerialPort(components))
    End Sub

    'Public methods
    # Attempts to connect to a Silverpak23CE using the PortName, BaudRate, and DriverAddress properties. 
    Returns True if successful.
    Throws an InvalidSilverpakOperationException if already connected.
    Public Function Connect() As Boolean
        SyncLock m_srlPort_lock
            'Validate SerialPort state
            if m_serialPortInterface_srlPort.IsOpen: raise InvalidSilverpakOperationException("Already connected.")
            try: 'except all expected exceptions
                'apply serial port settings
                m_serialPortInterface_srlPort.PortName = m_portName
                m_serialPortInterface_srlPort.BaudRate = m_baudRate
                'Attempt to connect
                m_serialPortInterface_srlPort.Open()
                'Check for a Silverpak23CE
                Dim response As String = writeAndGetResponse_srlPort(GenerateMessage(m_driverAddress, SafeQueryCommandStr), SafeQueryDelayFactor)
                if (response IsNot Nothing):
                    return True
                Else
                    closeSerialPort_srlPort()
                    return False
                End if
            except ex As ArgumentOutOfRangeException '.BaudRate
            except ex As ArgumentNullException '.PortName
            except ex As ArgumentException '.PortName
            except ex As UnauthorizedAccessException '.Open
            except ex As IO.IOException '.Write (called from within writeAndGetResponse_srlPort())
            End try:
            'Failed to connect. Make sure the SerialPort is closed
            closeSerialPort_srlPort()
            return False
        End SyncLock
    End Function
    Makes sure there is no active connection to a Silverpak23CE.
    Public Sub Disconnect()
        SyncLock m_srlPort_lock
            closeSerialPort_srlPort()
        End SyncLock
    End Sub

    Writes the passed complete message to the Silverpak23CE.
    Throws an InvalidSilverpakOperationException if not connected.
    <param name="completeMessage">Recommended use generateMessage() to generate this parameter.</param>
    <param name="delayFactor">How long the the Silverpak23CE is expected to take to process the message, 
    expressed as a multiple of PortDelatUnit, typically in the range 1.0 to 3.0.</param>
    Public Sub Write(ByVal completeMessage As String, ByVal delayFactor As Single)
        SyncLock m_srlPort_lock
            'Validate state
            if Not m_serialPortInterface_srlPort.IsOpen: raise InvalidSilverpakOperationException()
            'write message
            write_srlPort(completeMessage, delayFactor)
        End SyncLock
    End Sub

    Writes the passed message to and returns the body of the response from the Silverpak23CE.
    if no response was received, returns Nothing.
    Throws an InvalidSilverpakOperationException if not connected.
    <param name="completeMessage">Recommended use generateMessage() to generate this parameter.</param>
    <param name="delayFactor">How long the the Silverpak23CE is expected to take to process the message, 
    expressed as a multiple of PortDelatUnit, typically in the range 1.0 to 3.0.</param>
    Public Function WriteAndGetResponse(ByVal completeMessage As String, ByVal delayFactor As Single) As String
        SyncLock m_srlPort_lock
            'Validate state
            if Not m_serialPortInterface_srlPort.IsOpen: raise InvalidSilverpakOperationException()
            'write messag and get response
            return writeAndGetResponse_srlPort(completeMessage, delayFactor)
        End SyncLock
    End Function


    'Private fields
    # Contains sup-components.
    Private components As System.ComponentModel.IContainer

    # Field behind the PortName property.
    Private m_portName As String
    # Field behind the BaudRate property.
    Private m_baudRate As Integer
    # Field behind the DriverAddress property.
    Private m_driverAddress As DriverAddresses

    'Fields in the SyncLock group: srlPort
    # Lock object for the SyncLock group: srlPort.
    Private m_srlPort_lock As Object
    # The SerialPort object used to communicate with a Silverpak23CE. Part of the SyncLock group: srlPort.
    Private m_serialPortInterface_srlPort As SerialPort

    # The command for a safe query.
    Private Const m_safeQueryCommand As Commands = Commands.QueryControllerStatus
    # The operand for a safe query.
    Private Const m_safeQueryOperand As String = ""

    'Private methods
    # Disposes this component.
    Protected Overrides Sub Dispose(ByVal disposing As Boolean)
        try:
            if disposing AndAlso components IsNot Nothing:
                components.Dispose()
            End if
        Finally
            MyBase.Dispose(disposing)
        End try:
    End Sub

    Private Sub closeSerialPort_srlPort()
        if m_serialPortInterface_srlPort.IsOpen:
            try:
                m_serialPortInterface_srlPort.Close() 'Close the serial port.
            except 'Ignore any exceptions that occure while closing.
            End try:
        End if
    End Sub


    Writes the passed message to and returns the body of the response from the Silverpak23CE.
    if no response was received, returns Nothing.
    Part of the SyncLock group: srlPort.
    <param name="completeMessage">Recommended use generateMessage() to generate this parameter.</param>
    <param name="delayFactor">How long the the Silverpak23CE is expected to take to process the message, 
    expressed as a multiple of PortDelatUnit, typically in the range 1.0 to 3.0.</param>
    Private Function writeAndGetResponse_srlPort(ByVal completeMessage As String, ByVal delayFactor As Single) As String
        safeReadExisting_srlPort(0.0!) 'Clear the read buffer.
        safeWrite_srlPort(completeMessage, delayFactor) 'Write the message.
        Dim totalRx As String = "" 'accumulates chunks of RX data
        Do 'Read the response from the Silverpak23CE in chunks until the accumulated message is complete.
            Dim rxStr As String = safeReadExisting_srlPort(1.0!) 'Read a chunk.
            if rxStr Is Nothing OrElse rxStr = "": return Nothing 'if nothing came through, return nothing in lieu of an infinite loop.
            totalRx &= rxStr 'Append chunk to accumulated RX data.
        Loop while Not IsRxDataComplete(totalRx) 'check to see if the accumulated RX data is complete
        Dim trimResponse As String = TrimRxData(totalRx) 'Trim the RX data. Garunteed to succeed because IsRxDataComplete(totalRx) returned True
        return trimResponse.Substring(1) 'return only the return data (not the Status Char).
    End Function

    Writes the passed message to the Silverpak23CE.
    Part of the SyncLock group: srlPort.
    <param name="completeMessage">Recommended use generateMessage() to generate this parameter.</param>
    <param name="delayFactor">How long the the Silverpak23CE is expected to take to process the message, 
    expressed as a multiple of PortDelatUnit, typically in the range 1.0 to 3.0.</param>
    Private Sub write_srlPort(ByVal completeMessage As String, ByVal delayFactor As Single)
        safeWrite_srlPort(completeMessage, delayFactor)
    End Sub

    Reads the existing data on the read buffer from the Silverpak23CE after calling waitForSafeReadWrite_srlPort.
    In the event of an unexcepted exception from SerialPort.ReadExisting(), returns Nothing.
    Part of the SyncLock group: srlPort.
    <param name="delayFactor">How long to wait after reading from the Silverpak23CE,
    expressed as a multiple of PortDelatUnit, typically 1.0.</param>
    Private Function safeReadExisting_srlPort(ByVal delayFactor As Single) As String
        'wait for safe read/write
        waitForSafeReadWrite_srlPort(delayFactor)
        try: 'except any undocumented exceptions from SerialPort.ReadExisting()
            return m_serialPortInterface_srlPort.ReadExisting
        except
            return Nothing
        End try:
    End Function

    Writes the passed message to the Silverpak23CE after calling waitForSafeReadWrite_srlPort.
    Catches all exceptions from SerialPort.Write().
    Part of the SyncLock group: srlPort.
    <param name="completeMessage">Recommended use generateMessage() to generate this parameter.</param>
    <param name="delayFactor">How long the the Silverpak23CE is expected to take to process the message, 
    expressed as a multiple of PortDelatUnit, typically in the range 1.0 to 3.0.</param>
    Private Sub safeWrite_srlPort(ByVal completeMessage As String, ByVal delayFactor As Single)
        'wait for safe read/write
        waitForSafeReadWrite_srlPort(delayFactor)
        try: 'except any undocumented exceptions from SerialPort.Write()
            m_serialPortInterface_srlPort.Write(completeMessage)
        except
        End try:
    End Sub

    # Waits until the time passed by the last call to this method passes.
    Part of the SyncLock group: srlPort.
    <param name="incrementFactor">How long to wait after this call to this method,
    expressed as a multiple of PortDelatUnit, typically 1.0.</param>
    Private Sub waitForSafeReadWrite_srlPort(ByVal incrementFactor As Single)
        Static s_nextReadWriteTime As Integer = Environment.TickCount + incrementFactor * PortDelayUnit  'stores the next time that interaction with the Silverpak23CE is safe
        'wait until s_nextReadWriteTime
        Thread.Sleep(Math.Max(0, s_nextReadWriteTime - Environment.TickCount))
        'increment s_nextReadWriteTime by ReadWriteInterval number of milliseconds
        s_nextReadWriteTime = Environment.TickCount + PortDelayUnit * incrementFactor
    End Sub
End Class

'Friend modules
Consts and Functions for internal use
Friend Module SilverpakUtils

    # The beginning of a sent message to a Silverpak23CE.
    Friend Const DTProtocolTxStartStr As String = "/"
    # The end of a sent message to a Silverpak23CE.
    Friend Const DTProtocolTxEndStr As String = "R" & vbCr
    # The beginning of a received message from a Silverpak23CE.
    Friend Const DTProtocolRxStartStr As String = "/0"
    # The end of a received message from a Silverpak23CE.
    Friend Const DTProtocolRxEndStr As String = Chr(3)

    # DataBits setting for operating a Silverpak23CE over a serial port.
    Friend Const DTProtocolComDataBits As Integer = 8
    # Parity setting for operating a Silverpak23CE over a serial port.
    Friend Const DTProtocolComParity As IO.Ports.Parity = IO.Ports.Parity.None
    # StopBits setting for operating a Silverpak23CE over a serial port.
    Friend Const DTProtocolComStopBits As IO.Ports.StopBits = IO.Ports.StopBits.One
    # Handshake setting for operating a Silverpak23CE over a serial port.
    Friend Const DTProtocolComHandshake As IO.Ports.Handshake = IO.Ports.Handshake.None

    # Returns a complete message to write to the Silverpak23CE.
    <param name="commandList">Recommended use GenerateCommand() to generate this parameter. Multiple commands can be concatenated and passed as this argument.</param>
    Public Function GenerateMessage(ByVal recipient As DriverAddresses, ByVal commandList As String) As String
        return DTProtocolTxStartStr & GetDriverAddressStr(recipient) & commandList & DTProtocolTxEndStr
    End Function
    Returns a command to pass to GenerateMessage()
    Public Function GenerateCommand(ByVal cmnd As Commands, Optional ByVal operand As String = "") As String
        return GetCommandStr(cmnd) & operand
    End Function

    Returns the character to use in GenerateMessage()
    Public Function GetDriverAddressStr(ByVal driver As DriverAddresses) As String
        return Chr(driver)
    End Function

    Returns the string used in GenerateCommand()
    Public Function GetCommandStr(ByVal command As Commands) As String
        Select Case command
            'Homing and Positioning
            Case Commands.GoHome : return "Z"
            Case Commands.SetPosition : return "z"
            Case Commands.GoAbsolute : return "A"
            Case Commands.SetHomePolarity : return "f"
            Case Commands.GoPositive : return "P"
            Case Commands.GoNegative : return "D"
            Case Commands.SetPulseJogDistance : return "B"
            Case Commands.TerminateCommand : return "T"
            Case Commands.SetMotorPolarity : return "F"

                'Velocity and Acceleration
            Case Commands.SetVelocity : return "V"
            Case Commands.SetAcceleration : return "L"

                'Setting Current
            Case Commands.SetRunningCurrent : return "m"
            Case Commands.SetHoldCurrent : return "h"

                'Looping and Branching
            Case Commands.BeginLoop : return "g"
            Case Commands.EndLoop : return "G"
            Case Commands.Delay : return "M"
            Case Commands.HaltUntil : return "H"
            Case Commands.SkipIf : return "S"
            Case Commands.SetMode : return "n"

                'Position Correction - Encoder Option Only
            Case Commands.SetEncoderMode : return "N"
            Case Commands.SetPositionCorrectionTolerance : return "aC"
            Case Commands.SetEncoderRatio : return "aE"
            Case Commands.SetPositionCorrectionRetries : return "au"
            Case Commands.RecoverEncoderTimeout : return "r"

                'Program Stroage and Recall
            Case Commands.StoreProgram : return "s"
            Case Commands.ExecuteStoredProgram : return "e"

                'Program Execution
            Case Commands.RunCurrentCommand : return "R"
            Case Commands.RepeatCurrentCommand : return "X"

                'Microstepping
            Case Commands.SetMicrostepResolution : return "j"
            Case Commands.SetMicrostepAdjust : return "o"

                'On/Off Drivers (Outputs)
            Case Commands.SetOutputOnOff : return "J"

                'Query Commands
            Case Commands.QueryMotorPosition : return "?0"
            Case Commands.QueryStartVelocity : return "?1"
            Case Commands.QuerySlewSpeed : return "?2"
            Case Commands.QueryStopSpeed : return "?3"
            Case Commands.QueryInputs : return "?4"
            Case Commands.QueryCurrentVelocityModeSpeed : return "?5"
            Case Commands.QueryMicrostepSize : return "?6"
            Case Commands.QueryMicrostepAdjust : return "?7"
            Case Commands.QueryEncoderPosition : return "?8"
            Case Commands.ClearMemory : return "?9"

            Case Commands.QueryCurrentCommand : return "$"
            Case Commands.QueryFirmwareVersion : return "&"
            Case Commands.QueryControllerStatus : return "Q"
            Case Commands.TerminateCommands : return "T"
            Case Commands.EchoNumber : return "p"

                'Baud Control
            Case Commands.SetBaudRate : return "b"

            Case Else : raise ArgumentException("Unknown Enum Value", "command")
        End Select
    End Function

    # Evaluates an RX string received from the Silverpak and returns whether the RX message is complete and valid.
    Public Function IsRxDataComplete(ByVal rxData As String) As Boolean
        if rxData Is Nothing: return False 'rxData is Nothing
        if Not rxData.Contains(DTProtocolRxStartStr): return False 'rxData does not include Start
        return rxData.Substring(rxData.IndexOf(DTProtocolRxStartStr) + DTProtocolRxStartStr.Length).Contains(DTProtocolRxEndStr)
    End Function

    Returns just the status char and data from the passed RX message. Returns Nothing if RX data is incomplete or invalid.
    Public Function TrimRxData(ByVal rxData As String) As String
        if rxData Is Nothing: return Nothing 'rxData cannot be Nothing
        Dim iStart As Integer = rxData.IndexOf(DTProtocolRxStartStr)
        if iStart < 0: return Nothing 'rxData must include DTPROTOCOL_RX_STARTCHAR
        Dim fstTrim As String = rxData.Substring(iStart + DTProtocolRxStartStr.Length)
        Dim iLen As Integer = fstTrim.IndexOf(DTProtocolRxEndStr)
        if iLen < 0: return Nothing 'rxData must include DTPROTOCOL_RX_ENDCHAR after the DTPROTOCOL_RX_STARTCHAR
        return fstTrim.Substring(0, iLen)
    End Function

    Sets the DataBits, Parity, StopBits, and Handshake properties of the passed SerialPort object in accordance with DT Protocol.
    Public Function InitializeSerialPort(ByVal srlPort As SerialPort) As SerialPort
        With srlPort
            .DataBits = DTProtocolComDataBits
            .Parity = DTProtocolComParity
            .StopBits = DTProtocolComStopBits
            .Handshake = DTProtocolComHandshake
        End With
        return srlPort
    End Function

    Searches for available Silverpak23CE's and returns a PortInformation class for every serached COM port.
    if any parameters are not set, all possible values for the parameters will be attempted.
    This method can raise an ArgumentOutOfRangeException or an ArgumentException if passed values are invalid.
    Public Function SearchComPorts(Optional ByVal portName As String = SilverpakManager.DefaultPortname, Optional ByVal baudRate As Integer = SilverpakManager.DefaultBaudRate, _
                                   Optional ByVal driverAddress As DriverAddresses = SilverpakManager.DefaultDriverAddress) As PortInformation()
        if portName = SilverpakManager.DefaultPortname:
            'Search all COM ports
            Dim allPortNames() As String = SerialPort.GetPortNames()
            Dim rtnAry(allPortNames.Length - 1) As PortInformation
            For i As Integer = 0 To allPortNames.Length - 1
                'Search this COM port
                rtnAry(i) = SearchBaudRates(allPortNames(i), baudRate, driverAddress)
            Next
            return rtnAry
        Else
            'Search a specific COM port
            return PortInformation() {SearchBaudRates(portName, baudRate, driverAddress)}
        End if
    End Function
    Searches for an available Silverpak23CE at the specified COM port.
    if any parameters are not set, all possible values for the parameters will be attempted.
    This method can raise an ArgumentOutOfRangeException or an ArgumentException if passed values are invalid.
    Public Function SearchBaudRates(ByVal portName As String, Optional ByVal baudRate As Integer = SilverpakManager.DefaultBaudRate, _
                                    Optional ByVal driverAddress As DriverAddresses = SilverpakManager.DefaultDriverAddress) As PortInformation
        Dim portInfo As PortInformation = Nothing
        if baudRate = SilverpakManager.DefaultBaudRate:
            'Search all baud rates
            For Each iBaudRate As Integer In Integer() {9600, 19200, 38400}
                portInfo = SearchDriverAddresses(portName, iBaudRate, driverAddress)
                if portInfo IsNot Nothing: Exit For
            Next
        Else
            'Search specific baud rate
            portInfo = SearchDriverAddresses(portName, baudRate, driverAddress)
        End if
        if portInfo Is Nothing: portInfo = PortInformation With {.PortName = portName, .PortStatus = PortStatuses.Empty}
        return portInfo
    End Function
    Searches for an available Silverpak23CE at the specified COM port with the specified baud rate.
    if any parameters are not set, all possible values for the parameters will be attempted.
    Returns Nothing instead of a PortInformation with .PortStatus = Empty.
    This method can raise an ArgumentOutOfRangeException or an ArgumentException if passed values are invalid.
    Public Function SearchDriverAddresses(ByVal portName As String, ByVal baudRate As Integer, _
                                          Optional ByVal driverAddress As DriverAddresses = SilverpakManager.DefaultDriverAddress) As PortInformation
        if driverAddress = SilverpakManager.DefaultDriverAddress:
            'Search all driver addresses
            Dim allDriverAddresses() As DriverAddresses = [Enum].GetValues(GetType(DriverAddresses))
            Dim portInfo As PortInformation = Nothing
            For i As Integer = 1 To 16 'from Driver1 to Driver0 (includes Driver2 - Driver9, DriverA - DriverF)
                portInfo = GetSilverpakPortInfo(portName, baudRate, allDriverAddresses(i))
                if portInfo IsNot Nothing: Exit For
            Next
            return portInfo
        Else
            'Search specified driver address
            return GetSilverpakPortInfo(portName, baudRate, driverAddress)
        End if
    End Function
    Searches for an available Silverpak23CE at the specified COM port with the specified baud rate and driver address.
    Returns Nothing instead of a PortInformation with .PortStatus = Empty.
    This method can raise an ArgumentOutOfRangeException or an ArgumentException if passed values are invalid.
    Public Function GetSilverpakPortInfo(ByVal portName As String, ByVal baudRate As Integer, _
                                         ByVal driverAddress As DriverAddresses) As PortInformation
        Using sp As SerialPort = InitializeSerialPort(SerialPort())
            'set SerialPort parameters and allow exceptions to bubble out
            sp.PortName = portName
            sp.BaudRate = baudRate

            'delay if this method has been called recently
            Static s_nextSerialPortTime As Integer = Environment.TickCount + SilverpakConnectionManager.PortDelayUnit
            Thread.Sleep(Math.Max(0, s_nextSerialPortTime - Environment.TickCount))
            s_nextSerialPortTime = Environment.TickCount + SilverpakConnectionManager.PortDelayUnit

            'test the COM port
            try:
                'Open the serial port
                sp.Open() 'can raise UnauthorizedAccessException
                'Write a safe query
                sp.Write(GenerateMessage(driverAddress, SilverpakConnectionManager.SafeQueryCommandStr)) 'can raise IOException
                'read response
                Dim totalRx As String = "" 'accumulates chunks of RX data
                Do
                    Thread.Sleep(SilverpakConnectionManager.PortDelayUnit) 'wait for a chunk to be written to the read buffer
                    Dim newRx As String = sp.ReadExisting 'retrieve any data from the read buffer
                    if newRx = "": return Nothing 'abort if no data was written
                    totalRx &= newRx
                Loop while Not IsRxDataComplete(totalRx) 'check to see if the RX data is complete
                'success
                return PortInformation With {.PortName = portName, .BaudRate = baudRate, .DriverAddress = driverAddress, .PortStatus = PortStatuses.AvailableSilverpak}
            except ex As UnauthorizedAccessException 'thrown by .Open
                'Port was already open
                return PortInformation With {.PortName = portName, .PortStatus = PortStatuses.Busy}
            except ex As IO.IOException 'thrown by .Write
                'Port was invalid (such as a Bluetooth virtual COM port)
                return PortInformation With {.PortName = portName, .PortStatus = PortStatuses.Invalid}
            Finally
                'make sure the port is closed
                try:
                    if sp.IsOpen: sp.Close()
                except
                End try:
            End try:
        End Using
    End Function

End Module

'Friend enums
All available commands. See Specification Commands for more information.
Friend Enum Commands
    'Homing and Positioning
    # "Z"
    GoHome = 1
    # "z"
    SetPosition = 2
    # "A"
    GoAbsolute = 3
    # "f"
    SetHomePolarity = 4
    # "P"
    GoPositive = 5
    # "D"
    GoNegative = 6
    # "B"
    SetPulseJogDistance = 7
    # "T"
    TerminateCommand = 8
    # "F"
    SetMotorPolarity = 9

    'Velocity and Acceleration
    # "V"
    SetVelocity = 10
    # "A"
    SetAcceleration = 11

    'Setting Current
    # "m"
    SetRunningCurrent = 12
    # "h"
    SetHoldCurrent = 13

    'Looping and Branching
    # "g"
    BeginLoop = 14
    # "G"
    EndLoop = 15
    # "M"
    Delay = 16
    # "H"
    HaltUntil = 17
    # "S"
    SkipIf = 18
    # "n"
    SetMode = 19

    'Position Correction - Encoder Option Only
    # "N"
    SetEncoderMode = 20
    # "aC"
    SetPositionCorrectionTolerance = 21
    # "aE"
    SetEncoderRatio = 22
    # "au"
    SetPositionCorrectionRetries = 23
    # "r"
    RecoverEncoderTimeout = 24

    'Program Stroage and Recall
    # "s"
    StoreProgram = 25
    # "e"
    ExecuteStoredProgram = 26

    'Program Execution
    # "R"
    RunCurrentCommand = 27
    # "X"
    RepeatCurrentCommand = 28

    'Microstepping
    # "j"
    SetMicrostepResolution = 29
    # "o"
    SetMicrostepAdjust = 30

    'On/Off Drivers (Outputs)
    # "J"
    SetOutputOnOff = 31

    'Query Commands
    # "?0"
    QueryMotorPosition = 32
    # "?1"
    QueryStartVelocity = 33
    # "?2"
    QuerySlewSpeed = 34
    # "?3"
    QueryStopSpeed = 35
    # "?4"
    QueryInputs = 36
    # "?5"
    QueryCurrentVelocityModeSpeed = 37
    # "?6"
    QueryMicrostepSize = 38
    # "?7"
    QueryMicrostepAdjust = 39
    # "?8"
    QueryEncoderPosition = 40
    # "?9"
    ClearMemory = 41

    # "$"
    QueryCurrentCommand = 42
    # "&amp;"
    QueryFirmwareVersion = 43
    # "Q"
    QueryControllerStatus = 44
    # "T"
    TerminateCommands = 45
    # "p"
    EchoNumber = 46

    'Baud Control
    # "b"
    SetBaudRate = 47
End Enum

States for the motor
Friend Enum MotorStates
    # Serial Port is closed.
    Disconnected
    # Serial Port is just open.
    Connected
    # Motor settings have been written to the Silverpak23CE.
    InitializedSettings
    # Small movements have been issued to the Silverpak23CE to clear initialization quirks.
    InitializedSmoothMotion
    # In the process of moving to the zero position.
    InitializingCoordinates_moveToZero
    # The "official" homing command. should complete very quickly.
    InitializingCoordinates_calibrateHome
    # In the process of aborting coordinate initialization.
    AbortingCoordinateInitialization
    # Fully initialized and stopped.
    Ready
    # In the process of moving.
    Moving
End Enum



