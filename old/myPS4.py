import sys

from pyPS4Controller.controller import Controller, Event


class RemappedEvent(Event):
    def __init__(self, **kwargs):
        Event.__init__(self, **kwargs)
    
        self.keymap = dict(
            x=0 if not self.connecting_using_ds4drv else 1,
            circle=1 if not self.connecting_using_ds4drv else 2,
            triangle=2 if not self.connecting_using_ds4drv else 3,
            square=3 if not self.connecting_using_ds4drv else 0
        )

    def x_pressed(self):
        return self.button_id == self.keymap['x'] and self.button_type == 1 and self.value == 1

    def x_released(self):
        return self.button_id == self.keymap['x'] and self.button_type == 1 and self.value == 0

    def triangle_pressed(self):
        return self.button_id == self.keymap['triangle'] and self.button_type == 1 and self.value == 1

    def triangle_released(self):
        return self.button_id == self.keymap['triangle'] and self.button_type == 1 and self.value == 0

    def square_pressed(self):
        return self.button_id == self.keymap['square'] and self.button_type == 1 and self.value == 1

    def square_released(self):
        return self.button_id == self.keymap['square'] and self.button_type == 1 and self.value == 0

    def circle_pressed(self):
        return self.button_id == self.keymap['circle'] and self.button_type == 1 and self.value == 1

    def circle_released(self):
        return self.button_id == self.keymap['circle'] and self.button_type == 1 and self.value == 0


# Dummy funcions
def do_nothing(self, value=None): 
    """
    This functions does nothing. It is made to replace
    all event methods of the Controller class.
    """
    pass


class MuteController(Controller):

    def __init__(self, **kwargs):
        # Rewrite all methods in Controller class
        # to do nothing. Only the methods defined
        # below as methods will do anything.
        for attr in dir(Controller):
            if attr.startswith('on_'):  
                setattr(Controller, attr, do_nothing)
        # Run the initalisation to define the rest of
        # the attributes.
        Controller.__init__(self, **kwargs)
   

if __name__ == "__main__":
    usb = (len(sys.argv) > 1 and sys.argv[1] == '--usb')    
    controller = Controller(
        interface="/dev/input/js0",
        connecting_using_ds4drv=(not usb),
        event_definition=RemappedEvent,
        event_format="3Bh2b"
    )
    controller.listen()
