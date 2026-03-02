import serial
import time


class MockSerial:
    """Stand-in when no hardware is connected."""
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        print(f"[Serial] Hardware not found on {port} — using mock display")

    def write(self, data):
        text = data.decode('utf-8').strip()
        print(f"[DISPLAY] {text}")

    def close(self):
        pass


class SerialSender:
    """Manages a serial connection to a 16x2 LCD Arduino display.

    Call send_line(text) whenever the current lyric changes.
    Falls back to MockSerial if the port is unavailable.
    """

    LINE_WIDTH = 16

    def __init__(self, port: str = "COM11", baudrate: int = 9600, warmup: float = 2.0):
        self.port = port
        try:
            self.ser = serial.Serial(port, baudrate)
            print(f"[Serial] Connected to {port} at {baudrate} baud")
            time.sleep(warmup)   # let Arduino reset
        except (serial.SerialException, OSError):
            self.ser = MockSerial(port, baudrate)

    def _send_raw(self, line1: str, line2: str = ""):
        """Send two 16-char lines separated by '|', terminated with newline."""
        msg = line1.ljust(self.LINE_WIDTH)[:self.LINE_WIDTH] + "|" + \
              line2.ljust(self.LINE_WIDTH)[:self.LINE_WIDTH] + "\n"
        self.ser.write(msg.encode("utf-8"))

    def send_line(self, text: str):
        """Send a lyric line, splitting across both rows if needed."""
        text = text.replace('\n', ' ').strip()
        line1 = text[:self.LINE_WIDTH]
        line2 = text[self.LINE_WIDTH:self.LINE_WIDTH * 2] if len(text) > self.LINE_WIDTH else ""
        self._send_raw(line1, line2)

    def clear(self):
        """Blank both rows."""
        self._send_raw("", "")

    def close(self):
        self.ser.close()


if __name__ == "__main__":
    # Quick standalone test
    from spotifyFetch import getLyricsData
    sender = SerialSender()
    lyrics = getLyricsData('https://open.spotify.com/track/2u9S9JJ6hTZS3Vf22HOZKg')
    start  = time.time()
    for idx, item in enumerate(lyrics):
        target = start + item['startTime']
        while time.time() < target:
            time.sleep(0.01)
        sender.send_line(item['words'])
        print(item['words'])
