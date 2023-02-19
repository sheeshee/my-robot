"""
Test script to allow calibrating the position sensor.
"""
import time
import math
import pandas as pd

from pynput.keyboard import Key, Listener
import pyfirmata

myval = 90
step = 1

board = pyfirmata.Arduino('/dev/ttyACM')
it = pyfirmata.util.Iterator(board)
it.start()

current = board.get_pin('a:0:i')
position = board.get_pin('a:1:i')
servo = board.get_pin('d:5:s')


# initialise the pins with write/read
servo.write(myval)
position.read()
current.read()



def on_press(key):
    global myval
    if key == Key.up:
        if myval < 180:
            myval += step
    elif key == Key.down:
        if myval > 0:
            myval -= step
    else:
        pass


listener = Listener(on_press=on_press)
listener.start()

def get_current():
    return current.read()


def get_position(v_min, v_max):
    raw = position.read()
    # return raw
    pos = (raw - v_min) / (v_max - v_min) * 180
    return pos


def print_data(pos_min=0, pos_max=3.3):
    print(
        "CURRENT: %1.3f | POSITION: %3.1f | COMMAND: %3d" % (
            get_current(),
            get_position(pos_min, pos_max),
            myval
        )
    )


def multi_read(component, N):
    readings = []
    for i in range(N):
        value = component.read()
        if value:
            readings.append(value)
        # time.sleep(0.1)
    return sum(readings)/(len(readings))


def pre():
    # measure position at signal 0
    N = 100
    servo.write(180)
    time.sleep(3)
    v_max = multi_read(position, N)
    servo.write(0)
    time.sleep(3)
    v_min = multi_read(position, N)
    time.sleep(3)
    with open('data.csv', 'w') as f:
        f.write(f"{v_min}, {v_max}")

    return {'pos_min': v_min, 'pos_max': v_max}



def loop(pos_min, pos_max):
    while True:
        try:
            servo.write(myval)
            print_data(pos_min, pos_max)
        except KeyboardInterrupt:
            break

def post():
    print("\nScript exited.")


def measure(pos_min, pos_max):
    D = 180
    N = 10
    measurements = {}
    for d in range(D):
        servo.write(d)
        time.sleep(2)
        measurements[d] = sum([get_position(pos_min, pos_max) for _ in range(N)])/N

    data = pd.DataFrame(index=measurements.keys(), data={'x': measurements.values()})

    data.to_csv('measurements.csv')


if __name__ == "__main__":
    params = pre()
    # loop(**params)
    measure(**params)
    post()
