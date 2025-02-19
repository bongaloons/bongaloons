import serial
import threading
import queue
import time


class SerialHandler:
    def __init__(self, port='/dev/cu.usbmodem1101', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.last_press_time = {'left': 0, 'right': 0}
        self.BOTH_PRESS_THRESHOLD = 0.02  # 50ms threshold for simultaneous presses

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
                        current_time = time.time()
                        
                        if data == '0':
                            self.last_press_time['right'] = current_time
                            if (current_time - self.last_press_time['left']) < self.BOTH_PRESS_THRESHOLD:
                                print("Both sensors hit simultaneously!")
                                self.serial_queue.put('both')
                            else:
                                print("Hit detected on right sensor!")
                                self.serial_queue.put('right')
                                
                        elif data == '1':
                            self.last_press_time['left'] = current_time
                            if (current_time - self.last_press_time['right']) < self.BOTH_PRESS_THRESHOLD:
                                print("Both sensors hit simultaneously!")
                                self.serial_queue.put('both')
                            else:
                                print("Hit detected on left sensor!")
                                self.serial_queue.put('left')

        except serial.SerialException as e:
            print(f"Serial connection error: {e}")
            self.running = False

    def get_key(self):
        try:
            return self.serial_queue.get_nowait()
        except queue.Empty:
            return None 