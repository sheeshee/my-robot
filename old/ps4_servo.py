import time
import sys
from threading import Thread
import queue
from abc import abstractmethod
import numpy as np

import pyfirmata
from myPS4 import RemappedEvent, MuteController

DATUM = 90
CONT_SPEED = 10
POS_STEP = 1
SERVO_MIN = 0
SERVO_MAX = 180
QUEUE_MAXSIZE = -1


class Servo:
    def __init__(self, Interface, pin_number, identistring):
        self.pin = pin_number
        self.id = identistring
        self.servo = Interface.board.get_pin(f"d:{pin_number}:s")
        self.report_queue = Interface.report_queue
        self.queue = queue.Queue(QUEUE_MAXSIZE)
        self.thread = Thread(target=self.cable, daemon=True)
        self.thread.start()

    def send_to_cable(self, value):
        try:
            self.queue.put_nowait(value)
        except queue.Full:
            print('Queue Full for', self)
        else:
            pass

    def close_cable(self):
        self.queue.put('END')
        self.thread.join()

    def cable(self):
        direction = 0
        reference = DATUM
        while True:
            try:
                direction = self.queue.get_nowait()
                assert direction in [-1, 0, 1, 'END']
                if direction == 'END':
                    print('Closing cable for pin', self.pin)
                    return
            except queue.Empty:
                pass
            except queue.Full:
                pass
            finally:
                reference = self.move(reference, direction)
                assert reference is not None

    @abstractmethod
    def move(self, reference, direction):
        """
        Method to be overwritten telling the servo how to handle the
        given direction. The move method should call send_to_servo
        and return a reference value.
        """
        self.send_to_servo(DATUM)
        return DATUM

    def send_to_servo(self, value):
        if value > SERVO_MAX:
            capped = SERVO_MAX
        elif value < SERVO_MIN:
            capped = SERVO_MIN
        else:
            capped = value
        time.sleep(0.05)
        self.report_queue.put({'id': self.id, 'value': capped})
        self.servo.write(capped)

    def start_moving_clockwise(self):
        self.send_to_cable(1)

    def start_moving_counterclockwise(self):
        self.send_to_cable(-1)

    def stop(self):
        self.send_to_cable(0)


class Continuous(Servo):
    def __init__(self, Interface, pin, identistring):
        super(Continuous, self).__init__(Interface, pin, identistring)

    def move(self, reference, direction):
        self.send_to_servo(DATUM + direction*CONT_SPEED)
        return reference


class Positional(Servo):
    def __init__(self, Interface, pin, identistring):
        super(Positional, self).__init__(Interface, pin, identistring)

    def move(self, reference, direction):
        new_position = reference+direction*POS_STEP
        self.send_to_servo(new_position)
        return new_position


class AnalogueSensor:
    def __init__(self, Interface, pin_number, identistring):
        self.id = identistring
        self.report_queue = Interface.report_queue
        self.sensor = Interface.board.get_pin(f'a:{pin_number}:i')
        Thread(target=self.periodic_measurement, args=(0.1, ), daemon=True).start()

    def periodic_measurement(self, delay):
        while True:
            self.read()
            time.sleep(delay)

    def read(self):
        value = self.sensor.read()
        self.report_queue.put({'id': self.id, 'value': value})
        return value

class DummyBoard:
    def get_pin(self, pin):
        return DummyPin(pin)


class DummyPin():
    def __init__(self, pin):
        self.pin = pin

    def read(self):
        # print('Dummy Read - Pin', self.pin)
        return np.random.rand()

    def write(self, arg):
        # print('Dummy Write - Pin', self.pin, ':', arg)
        time.sleep(0.1)


class Roboface:
    def __init__(self, enabled=False):
        if enabled:
            self.board = pyfirmata.Arduino('/dev/ttyACM0')
            it = pyfirmata.util.Iterator(self.board)
            it.start()
        else:
            self.board = DummyBoard()

        self.report_queue = queue.Queue()

        self.current_sensors = [AnalogueSensor(self, k, f"A{k}") for k in range(2, 6)]

        self.base  = Continuous(self, 3, 'BASE') # board.get_pin('d:3:s')
        self.pivot = Positional(self, 5, 'PIVOT')
        self.elbow = Positional(self, 9, 'ELBOW')
        self.wrist = Positional(self, 10, 'WRIST')

    def read_current(self):
        currents = [s.read() for s in self.current_sensors]
        return currents, np.round(sum(currents), 4)

    def monitor(self):
        currents = [0, 0, 0, 0]
        base_speed = 0
        pivot_pos = 0
        elbow_pos = 0
        wrist_pos = 0
        while True:
            msg = self.report_queue.get()
            if msg['id'] == 'BASE':
                base_speed = msg['value']
            elif msg['id'] == 'PIVOT':
                pivot_pos = msg['value']
            elif msg['id'] == 'ELBOW':
                elbow_pos = msg['value']
            elif msg['id'] == 'WRIST':
                wrist_pos = msg['value']
            elif msg['id'] == 'A2':
                currents[0] = msg['value']
            elif msg['id'] == 'A3':
                currents[1] = msg['value']
            elif msg['id'] == 'A4':
                currents[2] = msg['value']
            elif msg['id'] == 'A5':
                currents[3] = msg['value']
            print(
                " ".join([
                    f"BASE:  {base_speed:3d}",
                    f"PIVOT: {pivot_pos:3d}",
                    f" ELBOW: {elbow_pos:3d}",
                    f"WRIST: {wrist_pos:3d}",
                    f"A2: {currents[0]:1.4f}",
                    f"A3: {currents[1]:1.4f}",
                    f"A4: {currents[2]:1.4f}",
                    f"A5: {currents[3]:1.4f}",
                    f"SUM: {sum(currents):1.4f}",
                ]),
                end='\r', flush=True
            )

    def stop(self):
        self.pivot.close_cable()
        self.elbow.close_cable()
        self.base.close_cable()
        self.wrist.close_cable()


class Controller(MuteController):

    def __init__(self, Roboface, use_ds4drv=True):
        MuteController.__init__(self,
            interface="/dev/input/js0",
            connecting_using_ds4drv=use_ds4drv,
            event_definition=RemappedEvent,
            event_format="3Bh2b"
        )
        self.robot = Roboface


    def on_x_press(self):
       self.robot.pivot.start_moving_counterclockwise()

    def on_x_release(self):
       self.robot.pivot.stop()

    def on_triangle_press(self):
        self.robot.pivot.start_moving_clockwise()

    def on_triangle_release(self):
        self.robot.pivot.stop()

    def on_square_press(self):
        self.robot.elbow.start_moving_clockwise()

    def on_square_release(self):
        self.robot.elbow.stop()

    def on_circle_press(self):
        self.robot.elbow.start_moving_counterclockwise()

    def on_circle_release(self):
        self.robot.elbow.stop()

    def on_up_arrow_press(self):
        self.robot.wrist.start_moving_clockwise()

    def on_down_arrow_press(self):
        self.robot.wrist.start_moving_counterclockwise()

    def on_up_down_arrow_release(self):
        self.robot.wrist.stop()

    def on_L1_press(self):
        self.robot.base.start_moving_clockwise()

    def on_L1_release(self):
        self.robot.base.stop()

    def on_R1_press(self):
        self.robot.base.start_moving_counterclockwise()

    def on_R1_release(self):
        self.robot.base.stop()


if __name__ == "__main__":
    usb = (len(sys.argv) > 1 and '--usb' in sys.argv)
    enabled = (len(sys.argv) > 1 and '--disable-safety' in sys.argv)

    robot = Roboface(enabled)
    controller = Controller(robot, not usb)

    Thread(target=controller.listen, daemon=True).start()


    try:
        print()
        robot.monitor()
    except KeyboardInterrupt:
        pass


    print('\nRunning last line')
