import os
import time
import struct
import datetime
import threading

# EVENT_SIZE = struct.calcsize("")

    
def do(interface):
    assert os.path.exists(interface), "Device must be connected"
    print('Connecting...', end='')
    handle = open(interface, "rb")
    print('done!')
    while True:
        try:
            read(handle)
        except KeyboardInterrupt:
            break
    print('Interrupted.')


def read(handle):
    raw = handle.read(8)
    *btime, value, btype, bid = struct.unpack("3Bh2b", raw)
 
    print(datetime.datetime.now(), end='')
    print(
        f"{value:7d}{btype:5d}{bid:3d} --- {btime}"
    )

if __name__ == "__main__":
    interface = "/dev/input/js0"
    do(interface)
