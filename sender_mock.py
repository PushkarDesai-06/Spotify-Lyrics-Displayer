import time
from spotifyFetch import getLyricsData

# Mock serial connection for testing without hardware
class MockSerial:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        print(f"Mock serial connection to {port} at {baudrate} baud")
    
    def write(self, data):
        text = data.decode('utf-8').strip()
        print(f"[MOCK DISPLAY] {text}")
    
    def close(self):
        print("Mock serial connection closed")

# Try to import and use real serial, fallback to mock
try:
    import serial
    ser = serial.Serial("COM11", 9600)
    print("Real serial connection established")
except:
    print("COM11 not found - using mock serial for testing")
    ser = MockSerial("COM11", 9600)

time.sleep(2)

def sendTwoLines(line1, line2=""):
    message = line1.ljust(16) + "|" + line2.ljust(16) + "\n"
    ser.write(message.encode("utf-8"))
    print(f"Sent: [{line1}] | [{line2}]")

def splitAndSend(text, time_available):
    splits = []
    while len(text) > 0:
        line1 = text[:16]
        line2 = text[16:32] if len(text) > 16 else ""
        splits.append((line1, line2))
        text = text[32:]

    delay_per_split = time_available / max(len(splits), 1)

    for (line1, line2) in splits:
        sendTwoLines(line1, line2)
        time.sleep(delay_per_split)

def startLyricsDisplay(lyrics):
    print("Starting lyric transfer...")
    start_time = time.time()

    for idx, item in enumerate(lyrics):
        target_time = start_time + item['startTime']

        while time.time() < target_time:
            time.sleep(0.01)

        sentence = item['words'].replace('\n', ' ')

        if idx < len(lyrics) - 1:
            next_time = lyrics[idx + 1]['startTime']
        else:
            next_time = item['startTime'] + 2  # fallback gap for last lyric

        time_available = max(next_time - item['startTime'], 0.1)

        splitAndSend(sentence, time_available)

    print("Finished lyric transfer.")

    