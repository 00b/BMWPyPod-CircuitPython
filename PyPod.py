import busio
import board
import time

def init(bdrate=19200):
    global iPodUart
    global MetaData
    global CmdReqs
    # global iPodName
    global PlayStatus
    global PlayChangeNotification
    global TrackIndex
    TrackIndex = 0
    PlayStatus = True
    PlayChangeNotification = False
    iPodMode = 0
    CmdReqs = []
    iPodUart = busio.UART(board.TX, board.RX, baudrate=bdrate, timeout=0.3)
    # iPodName = 'PyPod'

def MetaDataUpdate(NewMD):
    global MetaData
    MetaData = NewMD
    print('PyPod.MetaDataUpdate:')
    print(MetaData)
    return(MetaData)

def TrackChangeNotification(cmd=''):
    '''
    Send info to ipod iterface. Track index, position, length.
    Send update notification to ipod interface.
    -Track changed.
    -Play Status changes.
    -Seek
    etc
    '''
    global TrackIndex
    if cmd == 'TrackUpdate':
        TrackIndex = TrackIndex + 1
        if TrackIndex > 2:
            TrackIndex = 0
        #Send Playback track changed 0x01 New track record index (32 bits)
        #in the indexposh value shouldn't ever be more than 3 but if it is it should be fine.
        print('Sending Track Update. New TrackIndex ' + str(TrackIndex))
        Send(BuildiPodCmd([0x04],[0x00,0x27,0x01,(TrackIndex >> 24) & 0xff,(TrackIndex >> 16) & 0xff,(TrackIndex >> 8) & 0xff,TrackIndex & 0xff]))
    else:
        # May need to figure out how to better fake elasped time.
        # Maybe use a timer in the mainloop and pass it in as parameter.
        TrackElapsed = 5000
        # Break the TrackPosition into 4 bytes to send.
        # print('Sending update')
        elapsedbytes=[(TrackElapsed >> 24) & 0xff,(TrackElapsed >> 16) & 0xff, (TrackElapsed >> 8) & 0xff, TrackElapsed & 0xff]
        Send(BuildiPodCmd([0x04],[0x00,0x27,0x04] + elapsedbytes))

    # pass

def AddExtCmdReq(cmd):
    '''
    Add item to a pesudo event queue/command queue.
    '''
    global CmdReqs
    CmdReqs.append(cmd)
    # print('Add Command to Queue for processing:' + CmdReq)

def CmdReqsPending():
    '''
    Returns number of commands/requests in the queue.
    '''
    if len(CmdReqs) > 0:
        return(len(CmdReqs))
    else:
        return(False)

def GetExtCmdReq():
    '''
    Get item of event/command queue.
    Returns first items (0) from the list while removing it from the list.
    '''
    global CmdReqs
    if len(CmdReqs) > 0:
        return(CmdReqs.pop(0))

def Send(cmd):
    iPodUart.write(bytearray(cmd))

def GetCheckSum(val):
    '''
    Step 1 Put everthing in in a list as a byte
    Step 2 checksumer(thatlist)
    Step 3 checksum calculated and returned.
    '''
    checksum = [(0x100 - sum(val)) & 0xff]
    return(checksum)

def BuildiPodCmd(mode, cmd):
    '''
    Build responses/commands to queries/commands.
    prepends mode to sendthis variarble
    calculates length and prepends to sendthis
    gets checksum and appends to sendthis
    prepends 0xff 0x55 to sendthis.
    '''
    header = [0xFF, 0x55]
    serresp = mode+cmd
    serresp = [len(serresp)]+serresp
    serresp = serresp+GetCheckSum(serresp)
    serresp = header+serresp
    return(serresp)

def Ack(cmd):
    cmdlingo = cmd[1]
    if cmdlingo == 4:
        ack = [0x00,0x01,0x00,0x00]
        cmdacked = [cmd[3]]
    elif cmdlingo == 3:
        ack = [0x03,0x00,0x00]
        cmdacked = [cmd[2]]
    elif cmdlingo == 2:
        ack = [0x02,0x01,0x00]
        cmdacked = [cmd[2]]
    elif cmdlingo == 0:
        ack = [0x00,0x02,0x00]
        cmdacked = [cmd[2]]
    ack = ack+cmdacked
    # print('Mode/Lingo ' + str(cmd[3]) + ' ack')
    return(BuildiPodCmd([cmdlingo],ack))

def SetPlayStatus(val):
    global PlayStatus
    PlayStatus = val

def PlayControl(val):
    '''
    if playcontrol matches 1 3 4 Add the command to the
    command request and send an ack.
    Otherwise just send an ack back.
    '''
    Action=val[4]
    PlayControls = {1:'PlayPause',2:'Stop',3:'Next',4:'Prev',5:'FF',6:'RW',7:'FFRWEND'}
    print('PyPod.PlayControl: ' + PlayControls[Action])
    if Action == 1 or 2 or 3 or 4:
        AddExtCmdReq(PlayControls[Action])
    Send(Ack(val))

def GetMetaData(cmd):
    '''
    '''
    #Map command to request type and response.
    MDResp = {
        ' ' : {'Type' : 'Title' , 'Response' : [0x00,0x21]},
        '"' : {'Type' : 'Artist' , 'Response' : [0x00,0x23]},
        '$' : {'Type' : 'Album' , 'Response' : [0x00,0x25]},
        }
    RespType = MDResp[chr(cmd[3])]['Response']
    DataRequested = MetaData[MDResp[chr(cmd[3])]['Type']]
    print("MetaData Request: " + MDResp[chr(cmd[3])]['Type'] + ": " + DataRequested )
    DataRequested = list(DataRequested.encode())
    Terminator = [0x00]
    ToSend = RespType + DataRequested + Terminator
    Send(BuildiPodCmd([0x04],ToSend))

def GetIndexedPlayingInfo(cmd):
    '''
    Sends fake meta dat to ipod interface for:
    Genre resptype=[0x00,0x0D,0x05]
    Release Date resptype=[0x00,0x0D,0x02]
    Composer resptype=[0x00,0x0D,0x06]
    '''
    Terminator=[0x00]
    RespMap = {
        2: {'Type' : 'ReleaseDate', 'ResponseType': [0x00,0x0D,0x02], 'ResponseValue': [0x00,0x00,0x00,0x01,0x01,0x07,0xD0,0x06]},
        5: {'Type' : 'Genre', 'ResponseType': [0x00,0x0D,0x05], 'ResponseValue': 'Music'},
        6: {'Type' : 'Composer', 'ResponseType': [0x00,0x0D,0x06], 'ResponseValue' : 'Someone'},
        }
    DataRequested = RespMap[cmd[4]]['ResponseValue']
    RespType = RespMap[cmd[4]]['ResponseType']
    if type(DataRequested) is str:
        DataRequested = list(DataRequested.encode())
    ToSend = RespType + DataRequested + Terminator
    Send(BuildiPodCmd([0x04],ToSend))
    print('Get indexed Track info : ' + RespMap[cmd[4]]['Type'])

def GetRetrieveCategorizedDatabaseRecords(cmd):
    '''
    Send back fake playlist names and fake track names.
    '''
    Types = {
        1 : 'Playlist',
        2 : 'Artist',
        3 : 'Album',
        4 : 'Genre',
        5 : 'Track',
        6 : 'Composer',
        7 : 'Audiobook',
        8 : 'Podcast'}
    terminator = [0x00]
    resptype = [0x00,0x1B]
    startingpos = cmd[5:9]
    endpos = cmd[9:13]
    print('RetrieveCategorizedDatabaseRecords of type: ' + Types[cmd[4]])
    print('from : ' + str(int.from_bytes(startingpos,'big')) + ' to ' + str(int.from_bytes(endpos,'big')))
    if cmd[4] == 1:
        plnames=['128piPod','PL1','PL2'] #fake playlists
        for x in range(int.from_bytes(startingpos, 'big'), int.from_bytes(endpos, 'big')+1):
            print('PlayListName : ' + plnames[x])
            plnum = x.to_bytes(4, 'big')
            playlist = list(plnames[x].encode())
            playlist = list(plnum) + playlist
            ToSend = resptype + playlist + terminator
            Send(BuildiPodCmd([0x04], ToSend))

    elif cmd[4] == 5:
        tracknames = ['FakeTrack0','FakeTrack1','FakeTrack2']  #fake tracks for my fake ipod
        for x in range(int.from_bytes(startingpos,'big'), int.from_bytes(endpos,'big')):
        #for tracknum, tracks in enumerate(tracknames, start=0):
            tracknum = x.to_bytes(4,'big')
            track = list(tracknames[x].encode())
            track = list(tracknum) + track
            ToSend = resptype + track + terminator
            Send(BuildiPodCmd([0x04], ToSend))

    else:
        print('not yet implemented ' + Types[cmd[4]])

def GetNumberCategorizedDBRecords(cmd):
    '''
    Returns 0x02 for all types.
    '''
    pos = 4
    Types = {
            0x01 : 'Playlist',
            0x02 : 'Artists',
            0x03 : 'Album',
            0x04 : 'Genre',
            0x05 : 'Track',
            0x06 : 'Composer',
            0x07 : 'Audiobook',
            0x08 : 'Podcast'}
    resptype = [0x00,0x19]
    resp = [0x00,0x00,0x00,0x02]
    tosend = resptype + resp
    print('GetNumberCategorizedDBRecords : ' + Types[cmd[pos]])
    Send(BuildiPodCmd([0x04], tosend))

def SelectSortDBRecordBy(cmd):
    SortType = {
            0x00 : 'Genre',
            0x01 : 'Artist',
            0x02 : 'Composer',
            0x03 : 'Album',
            0x04 : 'Name',
            0x05 : 'Playlist',
            0x06 : 'ReleaseDate',
            0x07 : 'Reserved',
            0xFF : 'Default'}
    print('SelectSortDBRecords By: ' + SortType[cmd[9]] + 'Sending ACK')
    Send(Ack(cmd))

def GetCurrentPlayingTrackIndex():
        print('GetCurrentPlayingTrackIndex: ' + str(TrackIndex))
        resptype = [0x00,0x1F]
        # The better way to get 32bits into some bytes
        TrackNum = list(TrackIndex.to_bytes(4,'big'))
        # TrackNum = [(TrackIndex >> 24) & 0xff,(TrackIndex >> 16) & 0xff, (TrackIndex >> 8) & 0xff, TrackIndex & 0xff]
        if PlayStatus:
            Send(BuildiPodCmd([0x04], resptype + TrackNum))
        else:
            Send(BuildiPodCmd([0x04], resptype + [0xFF,0xFF,0xFF,0xFF]))

def GetPlayStatus():
    if PlayStatus:
        PlayStatusVal=[0x01]
        print('GetPlayStatus: Playing sending status 0x01 (playing)')
    else:  # if not playing paused
        PlayStatusVal=[0x02]
        print('GetPlayStatus: Not Playing sending status to 0x02 (paused)')
    resptype=[0x00,0x1D]
    tracklength = int(MetaData['Time(ms)'])
    # might need to fake play position better later for now. 5 seconds.
    playpos = 5000
    # The ugly way to enode to 32 bit bytes:
    tracklengthbytes=[(tracklength >> 24) & 0xff,(tracklength >> 16) & 0xff, (tracklength >> 8) & 0xff, tracklength & 0xff]
    playposbytes=[(playpos >> 24 ) &  0xFF,(playpos >> 16) & 0xff, (playpos >> 8) & 0xff, playpos & 0xff]
    ToSend = resptype + tracklengthbytes + playposbytes + PlayStatusVal
    Send(BuildiPodCmd([0x04],ToSend))

def SetPlayStatusChangeNotification(val):
    global PlayChangeNotification
    if val[4] == 1:
        PlayChangeNotification = True
    elif val[4] == 0:
        PlayChangeNotification = False
    Send(b'\xffU\x04\x04\x00&\x00\xd2')  # Ack?
    print ('Set PlayStatusChangeNotification: ' + str(PlayChangeNotification))
    # Send(Ack(val))

def ModeRequest(cmd):
    global iPodMode
    reqpos = cmd[2]
    ReqTypeMap = {
            0x03 : 'Request',
            0x04 : 'Return',
            0x05 : 'Enter',
            0x06 : 'Exit',
            }
    print (ReqTypeMap[reqpos] + 'RemoteUIMode')
    if ReqTypeMap[reqpos] == 'Request':
        print('Enter Extended UI Mode')
        iPodMode = 0x04
        resptype = [0x04]
        resp = list(iPodMode.to_bytes(1,'big'))
        tosend = resptype + resp
        Send(BuildiPodCmd([0x00],tosend))
        # AddExtCmdReq('play')
    elif ReqTypeMap[reqpos] == 'Return':
        print('This should not print')
    elif ReqTypeMap[reqpos] == 'Enter':
        print('Enter Extended UI Mode')
        iPodMode = 0x04
        Send(b'\xffU\x08\x00\x02\x06\x05\x00\x00\x0b\xb8(\xffU\x04\x00\x02\x00\x05\xf5')
        # print(Ack(cmd))
    elif ReqTypeMap[reqpos] == 'Exit':
        print('Exit Extended UI Mode')
        iPodMode = 0x00
        Send(Ack(cmd))

def CmdProcessor(cmd):
    '''
    This function is large and ugly.
    Does most of the work.
    '''
    PlayControlCMDs = b'\x04\x04\x00)'  #Start of playcontrol commands look like this.
    NumberCategorizedDBRecords = b'\x04\x04\x00\x18' #Start looks like this.
    RetrieveCategorizedDatabaseRecordsCmd = b'\x0c\x04\x00\x1a' #start looks like this.
    SelectSortDBRecord = b'\t\x04\x008\x01'
    IndexedPlayingInfo = b'\n\x04\x00\x0c'
    PlayStatusChangeNotificationCmds = b'\x04\x04\x00&'

    '''RetrieveCategorizedDatabaseRecordsCmds = [
        b'\x0c\x04\x00\x1a\x01\x00\x00\x00\x01\x00\x00\x00\x02\xd2', #MIGHT be an issue here
        b'\x0c\x04\x00\x1a\x05\x00\x00\x00\x00\x00\x00\x00\x02\xcf'] #may need to add some types here. 3 and 4?
    '''
    ModeRequests = [
        b'\x02\x00\x05\xf9',
        b'\x02\x00\x06\xf8',
        b'\x02\x00\x03\xfb',
        ]

    AckOnly = [
        b'\x03\x04\x00\x16\xe3',
        b'\x07\x04\x007\x00\x00\x00\x01\xbd']
    TrackDataRequests = [
        b'\x07\x04\x00 ',
        b'\x07\x04\x00"',
        b'\x07\x04\x00$']
    ReqPlayStatus = b'\x03\x04\x00\x1c\xdd'
    CurPlayingTrackIndex= b'\x03\x04\x00\x1e\xdb'

    # CommandMap = { command : function/response here? , nextcommand : function/response? }
    '''
    TODOs:

    likely more.
    '''
    '''
    Static Response Map:
    For commands that send the same response back each time.
    - Keeps the command, name and response close and readable.
    - Reduces if and elifs
    '''
    StaticRespMap = {
        b'\x03\x04\x00,\xcd' :
            {'Name' : 'GetShuffle',
            'Response' : b'\xffU\x04\x04\x00-\x00\xcb'},
        b'\x03\x04\x00/\xca' :
            {'Name' : 'GetRepeat',
            'Response' : b'\xffU\x04\x04\x000\x02\xc6'},
        b'\x03\x04\x003\xc6' :
            {'Name' : 'GetMonoDisplayImageLimits',
            'Response' : b'\xffU\x08\x04\x004\x016\x00\xa8\x01\xe0'},
        b'\x03\x04\x009\xc0' :
            {'Name' : 'GetColorDisplayImageLimits',
            'Response' : b'\xffU\r\x04\x00:\x016\x00\xa8\x02\x016\x00\xa8\x03\xf2'},
        b'\x03\x00\x0f\x00\xee' :
            {'Name' : 'RequestLingo0ProtocolVersion',
            'Response' : b'\xffU\x05\x00\x10\x00\x01\x06\xe4'},
        b'\x03\x00\x0f\x04\xea' :
            {'Name' : 'RequestLingo4ProtocolVersion',
            'Response' : b'\xffU\x05\x00\x10\x04\x01\x0c\xda'},
        b'\x03\x00\x0f\n\xe4' :
            {'Name' : 'RequestLingo0AProtocolVersion',
            'Response' : b'\xffU\x05\x00\x10\n\x01\x01\xdf'},
        b'\x0e\x00\x13\x00\x00\x00\x11\x00\x00\x00\x00\x00\x00\x00\x00\xce' :
            {'Name' : 'IdentifyDeviceLingoes',
            'Response' : b'\xffU\x04\x00\x02\x00\x13\xe7\xffU\x03\x00\'\x00\xd6'},
        b'\x02\x00$\xda' :
            {'Name' : 'RequestiPodOptions',
            'Response' : b'\xffU\n\x00%\x00\x00\x00\x00\x00\x00\x00\x01\xd0'},
        b'\x02\x00\t\xf5' :
            {'Name' : 'RequestiPodSoftwareVersion',
            'Response' : b'\xffU\x05\x00\n\x01\x03\x00\xed'},
        b'\x03\x04\x00\x12\xe7' :
            {'Name' : 'RequestProtocolVersion',
            'Response' : b'\xffU\x05\x04\x00\x13\x01\x0c\xd7'},
        b'\x02\x00\x0b\xf3' :
            {'Name' : 'RequestiPodSerialNum',
            'Response' : b'\xffU\x0e\x00\x0c8K644SQVV9R\x00\xea'},
        b'\x02\x00\r\xf1' :
            {'Name' : 'RequestiPodModelNum',
            'Response' : b'\xffU\x0e\x00\x0e\x00\x0b\x00\x11MA450LL\x00\t'},
        b'\x03\x04\x005\xc4' :
            {'Name' : 'GetNumPlayingTracks',
            'Response' : b'\xffU\x07\x04\x006\x00\x00\x00\x02\xbd'},
        b'\x02\x00\x07\xf7' :
            {'Name' : 'RequestiPodName(Mode0)',
            'Response' : b'\xffU\n\x00\x08128iPod\x00\xc7'},
        b'\x03\x04\x00\x14\xe5' :
            {'Name' : 'RequestiPodName(Mode4)',
            'Response' : b'\xffU\x0b\x04\x00\x15128iPod\x00\xb5'},
        b'\x03\x00\x01\x04\xf8' :
            {'Name' : 'Identify',
            'Response' : ''},
        b'\x07\x00(\x00\x00\x00\x00\x01\xd0' :
            {'Name' : 'RetAccessoryInfo',
            'Response' : ''}
        }
    CommandMap ={}

    cmd = cmd[2:]  #drop the xffU from the bytearray.

    if cmd in AckOnly:
        print('Responding with an ACK to ' + str(cmd))
        #  + ' with Ack ' + print(str(Ack(cmd))))
        Send(Ack(cmd))
    elif cmd in ModeRequests:
        ModeRequest(cmd)

    elif cmd in StaticRespMap:
        print(StaticRespMap[cmd]['Name'])
        Send(StaticRespMap[cmd]['Response'])
        if StaticRespMap[cmd]['Name'] == 'RequestProtocolVersion':
            print('Increaseing baudrate to 57600')
            iPodUart.baudrate=57600
            #print(iPodUart.baudrate)

        # if StaticRespMap[cmd]['Name'] == 'Identify':
        #    iPodMode = 0x04

    elif cmd.startswith(RetrieveCategorizedDatabaseRecordsCmd):
        GetRetrieveCategorizedDatabaseRecords(cmd)

    elif cmd.startswith(SelectSortDBRecord):
        SelectSortDBRecordBy(cmd)

    elif cmd.startswith(NumberCategorizedDBRecords):
        GetNumberCategorizedDBRecords(cmd)

    elif cmd.startswith(PlayControlCMDs):
        PlayControl(cmd)

    elif cmd.startswith(PlayStatusChangeNotificationCmds):
        SetPlayStatusChangeNotification(cmd)

    elif cmd.startswith(IndexedPlayingInfo):
        GetIndexedPlayingInfo(cmd)

    elif any(map(cmd.startswith, TrackDataRequests)):
        GetMetaData(cmd)

    elif cmd == ReqPlayStatus:
        GetPlayStatus()

    elif cmd == CurPlayingTrackIndex:
        GetCurrentPlayingTrackIndex()

    else:
        print(cmd + ' sending an Ack cause nothing else got this')
        Send(Ack(cmd))

def ReadCommand():
    '''
    Read from the iPodUart and extract any commands that come across.
    Read 1 byte. if it is 0xFF then read next byte.
    if next byte 0x55 we have a command header.
    Then read rest of command.
    This section could likely be far more elegant but it works...
    '''
    if iPodUart.read(1) == b'\xff':
        if iPodUart.read(1) == b'\x55':
            iPodCommand = [b'\xff\x55']
            cmddata = iPodUart.read(2)  # get length and command
            iPodCommand.append(cmddata)
            cmdlen = cmddata[0]
            cmddata = iPodUart.read(cmdlen)  # get the rest of the command.
            iPodCommand.append(cmddata)
            fullcmd = iPodCommand[0] + iPodCommand[1] + iPodCommand[2]
            # print(fullcmd)
            return(fullcmd)