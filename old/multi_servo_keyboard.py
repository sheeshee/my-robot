# If pynput raises error, set this:
# DISPLAY=":0" python my-script.py

import time
import os
os.environ["DISPLAY"] = ":0"

import numpy as np

from pynput.keyboard import Key, Listener
import pyfirmata

pos_base = 90
pos_pivot = 90
pos_elbow = 90
pos_wrist = 90

step = 1

def on_press(key):
    global pos_base, pos_elbow, pos_pivot, pos_wrist
    if key == Key.up:
        pos_pivot += step
    elif key == Key.down:
        pos_pivot -= step
    elif key == Key.left:
        pos_base += step
    elif key == Key.right:
        pos_base -= step
    elif key.char == 'a':
        pos_elbow += step
    elif key.char == 'd':
        pos_elbow -= step
    elif key.char == 'w':
        pos_wrist += step
    elif key.char == 's':
        pos_wrist -= step
    else:
        print(key)


def on_release(key):
    global pos_base
    pos_base = 90

def C(current):
    return np.round(sum([c.read() for c in current]), 2)

board = pyfirmata.Arduino('/dev/ttyACM0')
it = pyfirmata.util.Iterator(board)
it.start()

current = [board.get_pin(f'a:{k}:i') for k in range(2, 6)]

base = board.get_pin('d:11:s')
pivot = board.get_pin('d:10:s')
elbow = board.get_pin('d:9:s')
wrist = board.get_pin('d:6:s')

listener = Listener(on_press=on_press)
listener.start()

while True:
    try:
        print(C(current), '-', pos_base, pos_pivot, pos_elbow, pos_wrist)
        base.write(pos_base)
        pivot.write(pos_pivot)
        elbow.write(pos_elbow)
        wrist.write(pos_wrist)
    except KeyboardInterrupt:
        break


listener.stop()
print('\nScript exited.')
