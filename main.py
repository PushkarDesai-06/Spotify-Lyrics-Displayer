import string
import serial
import time
import datetime
from spotifyFetch import getLyricsData

ser = serial.Serial("COM11", 9600)
print(ser.name)


def findCOM():
    for i in range():
        try:
            ser = serial.Serial(f"COM{i}" , 9600)
        except:
            print("error")


def encodeStr(str: string):
    return str.encode("utf-8")

def sendStr(str):

    temp = str
    if(len(temp) > 16):
        temp = temp[:16] + '\n' + temp[16:]
    ser.write(encodeStr(temp))

def sendNumbers():
    time.sleep(2)
    sendStr('Starting...')
    time.sleep(2)
    i = 0
    while 1:
        sendStr(str(i))
        i += 1
        time.sleep(1)

def initClock():
    time.sleep(2)
    while 1:
        current_datetime = datetime.datetime.now()
        formatted_time = current_datetime.strftime("%H:%M:%S")
    # if(int(formatted_time[0:2]) > 12):
    #   formatted_time += "PM"
    # else:
    #   formatted_time += "AM"
        sendStr(formatted_time)
        time.sleep(1)


def initTransfer():
    while 1:
        time.sleep(1)
        sendStr('Wassup!')

def startLyricsTransfer():
    lyrics = getLyricsData('https://open.spotify.com/track/0AAMnNeIc6CdnfNU85GwCH?si=da2afe08a6724759')
    print('fetched....')  
    for i in lyrics:
        time.sleep(i['startTime'])
        sentence = i['words']
        sendStr(sentence)
        print(i['words'])


# sendNumbers()

############################# START HERE #############################



startLyricsTransfer()

