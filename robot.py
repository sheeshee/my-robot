from textual.app import App, ComposeResult, RenderResult
from textual.containers import Horizontal
from textual.widgets import Static, Label
from textual.reactive import reactive
import pyfirmata
from threading import Thread
import random
import time


MOCK = True

if MOCK is False:
    board = pyfirmata.Arduino('/dev/ttyACM0')
    it = pyfirmata.util.Iterator(board)
    it.start()
else:
    board = None


class MockPin:
    def write(self, var):
        pass

    def read(self):
        return round(random.random(), 4)


class Joint:
    def __init__(self, board, str_code, start=90, mock=False):
        self.pos = start
        if mock:
            self.pin = MockPin()
        else:
            self.pin = board.get_pin(str_code)
            self.pin.write(self.pos)

    def write(self, val):
        self.pin.write(val)


class ValueLabel(Label):

    pos = reactive(-1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self):
        return f"{self.pos}"


class RobotController(App):

    CSS_PATH = "robotcontroller_layout.css"

    segment_labels = [
        ("base", "Q", "W", "d:11:s", 90),
        ("link1", "A", "S", "d:10:s", 0),
        ("link2", "Z", "X", "d:9:s", 180),
        ("link3", "I", "O", "d:6:s", 180),
        ("headtwist", "J", "K", "d:5:s", 90),
        ("claw", "N", "M", "d:3:s", 90)
    ]

    segments = {
        label[0]: ValueLabel(classes="box key_value")
        for label in segment_labels
    }

    joints = {
        label[0]: Joint(board, label[3], start=label[4], mock=MOCK)
        for label in segment_labels
    }

    volt_disp = ValueLabel(classes="box key_value")
    curr_disp = ValueLabel(classes="box key_value")
    base_disp = ValueLabel(classes="box key_value")
    base_disp_deg = ValueLabel(classes="box key_value")

    if MOCK:
        current = MockPin()
        voltage = MockPin()
        base_res = MockPin()
    else:
        current = board.get_pin("a:0:i")
        voltage = board.get_pin("a:1:i")
        base_res = board.get_pin("a:2:i")

    def read_power(self):
        while True:
            self.curr_disp.pos = round((self.current.read() - 0.5) * 2.5, 2)
            self.volt_disp.pos = round(self.voltage.read() * 10, 2)
            self.base_disp.pos = round(self.base_res.read() * 5, 2)
            self.base_disp_deg.pos = round((self.base_res.read() - 0.064) / (0.58 - 0.064) * 180, 0)
            # max 0.58
            # min 0.064
            time.sleep(0.5)

    def compose(self) -> ComposeResult:
        Thread(target=self.read_power, daemon=True).start()

        for label in self.segment_labels:
            self.segments[label[0]].pos = label[4]
            yield Horizontal(
                    Static(label[0].title(), classes="box segment_label"),
                    Static(label[1], classes="box key_label"),
                    self.segments[label[0]],
                    Static(label[2], classes="box key_label"),
                    classes="controller"
                )
        yield Horizontal(
            Static("Voltage", classes="box segment_label"),
            self.volt_disp,
            Static("Current", classes="box segment_label"),
            self.curr_disp,
            Static("Position (V)", classes="box segment_label"),
            self.base_disp,
            Static("(deg)", classes="box segment_label"),
            self.base_disp_deg
        )

    def up(self, segment):
        self.update(segment, 1)

    def down(self, segment):
        self.update(segment, -1)

    def update(self, segment, step):
        new_val = self.segments[segment].pos + step
        new_val = max(min(180, new_val), 0)
        self.segments[segment].pos = new_val
        self.joints[segment].write(new_val)

    def key_q(self):
        self.up("base")

    def key_w(self):
        self.down("base")

    def key_a(self):
        self.up("link1")

    def key_s(self):
        self.down("link1")

    def key_z(self):
        self.up("link2")

    def key_x(self):
        self.down("link2")

    def key_i(self):
        self.up("link3")

    def key_o(self):
        self.down("link3")

    def key_j(self):
        self.up("headtwist")

    def key_k(self):
        self.down("headtwist")

    def key_n(self):
        self.up("claw")

    def key_m(self):
        self.down("claw")
