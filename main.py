import RN52  # for interfacing with the RN52 board.
import PyPod  # python ipod emulator (port this shit also fix it/improve it).
import time
import board
# import busio
from digitalio import DigitalInOut, Direction, Pull

'''
GPIO stuff:
Setup 2 GPIO PINs.
- 1) output to RN52 to be in command mode. Set high for command mode.
- 2) input to monitor GPIO2 on RN52 (change flag/inicator).
    Pulled low to indicate change.
'''
CommandMode = DigitalInOut(board.D13)
CommandMode.direction = Direction.OUTPUT
CommandMode = True

ChangeFlag = DigitalInOut(board.D7)
ChangeFlag.direction = Direction.INPUT
ChangeFlag.pull = Pull.UP

'''
Initialize things.
'''

# Init the RN52 and PyPod modules.
# This brings up the UART/Serial interface in each.
RN52.RN52init()
time.sleep(2)
PyPod.init()

# Get some metadata. Might be dummy data but its
# something stored to be used later.
MetaData = RN52.GetMetaData()
# Push the metadata to the ipod module.
PyPod.MetaDataUpdate(MetaData)
# print(time.monotonic())
print(MetaData)

# Get Connection Status.
RN52Status = RN52.GetStatus()
print('inital status : ' + str(RN52Status))
if RN52Status[3] == 'D':
    print('Playing')
    # PyPod.SetPlayStatus(True)
else:
    print('Not Playing')
    # PyPod.SetPlayStatus(False)
# print('PlayStatus: ' + str(PyPod.PlayStatus))

if RN52Status[1] == '0':
    MetaData['Title'] = 'Not Connected'
print(MetaData)

'''
Check status of ChangeFlag Input pin.
Inverting flag value as its based on an input state being true or false.
where low indicates false indicates change.
'''
def ChangeCheck():
    if ChangeFlag.value is False:
        return(True)
    else:
        return(False)

'''
Process Command Reqests.
if a play control command then send it.
can build out more commands later.
'''
def ProcessCmdReq(cmd):
    cmd = cmd.lower()
    if cmd == 'playpause' or cmd == 'next' or cmd == 'prev':
        print('PlayCommand: ' +  cmd)
        if cmd == 'playpause' and PyPod.PlayStatus is True:
            PyPod.PlayStatus = False
        else:
            PyPod.PlayStatus = True

        if cmd == 'next' or cmd == 'prev':
            PyPod.TrackChangeNotification('TrackUpdate')


        if RN52.PlayControl(cmd):
            return (True)
        else:
            return (False)

'''
Main loop.
'''
StartTime = round(time.monotonic() * 1000)
UpdateTimer = StartTime
MDTimer = StartTime
while(True):
    #elapsed = round(time.monotonic() * 1000 - StartTime)
    if time.monotonic() * 1000 - UpdateTimer > 500 and PyPod.PlayChangeNotification:
        PyPod.TrackChangeNotification()
        UpdateTimer = round(time.monotonic() * 1000)

    #Force check for MetaData update once every minute.
    if time.monotonic() * 1000 - MDTimer > 60000:
        print('Checking Stored MetaData against RN52 MetaData')
        NewMD = RN52.GetMetaData()
        if NewMD != MetaData:
            print('MetaData changed: sending track update')
            MetaData = NewMD
            PyPod.MetaDataUpdate(MetaData)
            PyPod.TrackChangeNotification('TrackUpdate')
        MDTimer = round(time.monotonic() * 1000)

    if PyPod.MetaData != MetaData:
        PyPod.MetaDataUpdate(MetaData)
        PyPod.TrackChangeNotification('TrackUpdate')

    if ChangeCheck():
        NewStatus = RN52.GetStatus()
        print('Change detected: ' + str(RN52Status) + ' to ' + str(NewStatus))

        if NewStatus != RN52Status:
            if NewStatus[0] == '2':
                NewMD = RN52.GetMetaData()
                while NewMD == MetaData:
                    print('Updating MetaData')
                    NewMD = RN52.GetMetaData()
                MetaData = NewMD
                PyPod.MetaDataUpdate(NewMD)
                PyPod.TrackChangeNotification('TrackUpdate')
            if NewStatus[3] == 'D' and RN52Status[3] == '3':
                print('Play Status changed to: Playing')
                PyPod.SetPlayStatus(True)
            if NewStatus[3] == '3' and RN52Status[3] == 'D':
                print('Play Status changed to: Not Playing')
                # PyPod.SetPlayStatus(False)
            if NewStatus[1] == '4' and RN52Status[1] == '0':
                print('Connection Status changed to: Connected')
            if NewStatus[1] == '0' and RN52Status[1] == '4':
                print('Connection status changed to: Not connected')
                MetaData['Title'] = 'Not Connected'
        # reset status as the track change flag changes back after query.
        RN52Status = RN52.GetStatus()

    iPodcommand = PyPod.ReadCommand()
    if iPodcommand:
        PyPod.CmdProcessor(iPodcommand)
    # Check if there are any Command Requests from the ipod iterface
    # Next Track, Play, ETC, MetaDataUpdate...
    if PyPod.CmdReqsPending():
        ProcessCmdReq(PyPod.GetExtCmdReq())