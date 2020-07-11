import busio
import board
import time

def RN52init():
    global RN52Uart
    RN52Uart = busio.UART(board.A4, board.A5, baudrate=115200,timeout=.4)
    time.sleep(.5)

def Send(cmd):
    RN52Uart.reset_input_buffer()  # clear the input buffer.
    RN52Uart.write(bytearray(cmd))  # send the command.
    Response = RN52Uart.read()  # read the input buffer for a response.
    return(Response)

def GetStatus():
    command = 'Q\n'
    #resp = Send(command)
    RN52Uart.reset_input_buffer()  # clear the input buffer.
    RN52Uart.write(bytearray(command))
    resp = RN52Uart.readline()  #read a line not a bunch of stuff.
    if resp.endswith('\r\n'):
        resp=resp[:-2]
        resp=resp.decode('utf-8')
    return(resp)

def GetMetaData():
    RN52Uart.timeout = 1
    MetaData = {}
    command = 'AD\n'
    resp = Send(command)
    if len(resp) > 5:
        resp = resp.decode('utf-8')
    else:  # placeholder response.
        resp = 'AOK\r\nTitle=Unknown\r\r\nArtist=Unknown\r\r\nAlbum=Unknown\r\r\nTrackNumber=1\r\r\nTrackCount=99\r\r\nTime(ms)=100000\r\r\n'
    # re-format the response.
    splits = resp.splitlines()
    # remove the empty list items caused by the all th extra \r's and \ns in the respons.
    splits[:] = [item for item in splits if item != '']
    for item in splits:  # Put the stuff into a dictonary.
        if '=' in item:
            MetaData[item.split('=')[0]] = item.split('=')[1]
    RN52Uart.timeout = .4
    return(MetaData)

def PlayControl(cmd):
    if cmd.lower() == 'next':
        command='AT+\n'
    elif cmd.lower() == 'prev' or cmd.lower() == 'previous':
        command='AT-\n'
    elif cmd.lower() == 'play' or cmd.lower() == 'pause' or cmd.lower() == 'playpause' or cmd.lowe() == 'stop':
        command = 'AP\n'
    resp=Send(command)
    if resp == b'AOK\r\n':
        return(True)
    else:
        return(False)