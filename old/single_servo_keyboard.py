# If pynput raises error, set this:
# DISPLAY=":0" python my-script.py

import time
import os
os.environ["DISPLAY"] = ":0"

from pynput.keyboard import Key, Listener
import pyfirmata

myval = 90
step = 1

def on_press(key):
    global myval
    if key == Key.up:
        myval = min(myval + step, 180)
    elif key == Key.down:
        myval = max(myval - step, 0)
    else:
        pass



board = pyfirmata.Arduino('/dev/ttyACM0')
it = pyfirmata.util.Iterator(board)
it.start()

current = board.get_pin('a:0:i')
position = board.get_pin('a:1:i')
servo = board.get_pin('d:5:s')

listener = Listener(on_press=on_press)
listener.start()

while True:
    try:
        print(current.read(), '-', position.read(), '-', myval)
        servo.write(myval)
        time.sleep(0.1)
    except KeyboardInterrupt:
        break


listener.stop()
print('\nScript exited.')
