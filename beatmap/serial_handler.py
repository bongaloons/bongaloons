import serial
import threading
import queue
import time

class SerialHandler:
    def __init__(self, port='/dev/cu.usbmodem101', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_queue = queue.Queue()
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._read_serial)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _read_serial(self):
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                while self.running:
                    if ser.in_waiting:
                        data = ser.readline().decode('utf-8').strip()
                        if data == '0':
                            print("Hit detected on right sensor!")
                            self.serial_queue.put('l')  # right
                        elif data == '1':
                            print("Hit detected on left sensor!")
                            self.serial_queue.put('a')  # left

        except serial.SerialException as e:
            print(f"Serial connection error: {e}")
            self.running = False

    def get_key(self):
        try:
            return self.serial_queue.get_nowait()
        except queue.Empty:
            return None 