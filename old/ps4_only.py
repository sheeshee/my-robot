import sys

from myPS4 import RemappedEvent, MuteController


class MyController(MuteController):

    def __init__(self, **kwargs):
        MuteController.__init__(self, **kwargs)        

    def on_x_press(self):
       print("Hello world")

    def on_x_release(self):
       print("Goodbye world")
    
    def on_L3_left(self, value):
        print("L3LEFT", value)

    def on_L3_right(self, value):
        print("L3RIGHT", value)


if __name__ == "__main__":
    usb = (len(sys.argv) > 1 and sys.argv[1] == '--usb')    
    controller = MyController(
        interface="/dev/input/js0",
        connecting_using_ds4drv=(not usb),
        event_definition=RemappedEvent,
        event_format="3Bh2b"
    )
    controller.listen()
