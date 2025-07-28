from akai_pro_py import controllers
from soundcraft_ui16 import MixerSender
from mido import get_output_names
from time import sleep
from re import match
from logging import getLogger
from threading import Thread, Event
from queue import Queue
from argparse import Namespace
from services.config import APC_DISCOVER_STRING, Config, MASTER_LOCK
from services.formatter import ConfigVars


class ApcControllerThread:
    def __init__(
        self,
        apc_queue: Queue,
        gui_queue: Queue,
        midimix_queue: Queue,
        sender: MixerSender,
        config: Config,
        args: Namespace,
        logger_name: str = "APC"
    ) -> None:
        self.logger = getLogger(logger_name)
        self.args = args
        self.midi_string = self.get_midi_string(APC_DISCOVER_STRING)
        self.sender = sender
        self.apc_queue = apc_queue
        self.gui_queue = gui_queue
        self.midimix_queue = midimix_queue
        self.config = config
        self.apc = None
        self.keepalive_thread = Thread(
            target=self._thread,
            args=()
        )
        self.exit_flag = Event()

    def get_midi_string(self, search) -> str:
        for port in get_output_names():
            matching = match(search, port)
            if matching:
                return matching.group()
        return None

    def _thread(self) -> None:
        while not self.exit_flag.is_set():
            if not self.midi_string:
                self.logger.warning("No Port for APC found")
                self.midi_string = \
                    self.get_midi_string(APC_DISCOVER_STRING)
                sleep(.5)
                continue
            if (
                not self.apc
                or (
                    self.apc
                    and self.apc.ready
                    and self.apc.is_alive()
                )
            ):
                try:
                    self.apc = APC(
                        self.midi_string, self.apc_queue,
                        self.gui_queue, self.midimix_queue, self.sender,
                        self.config, self.args, self.logger.name
                    )
                    # Drain Queue and send init request
                    while self.apc_queue.qsize() > 0:
                        self.apc_queue.get()
                    self.apc_queue.put({"key": "init"})
                    self.logger.warning(f"{self.apc.name} => created!")
                    self.apc.start()
                except:  # noqa: E722
                    self.logger.critical("APC => failed!")

    def start(self) -> None:
        self.keepalive_thread.start()

    def join(self) -> None:
        self.keepalive_thread.join()

    def terminate(self) -> None:
        self.exit_flag.set()
        self.join()


class APC(controllers.APCMinimkii):
    def __init__(
        self,
        midi_string: str,
        apc_queue: Queue,
        gui_queue: Queue,
        midimix_queue: Queue,
        sender: MixerSender,
        config: Config,
        args: Namespace,
        logger_name: str = "APC"
    ) -> None:
        super().__init__(midi_string, midi_string)
        self.args = args
        self.midi_string = midi_string
        self.logger = getLogger(logger_name)
        self.sender = sender
        self.config = config
        self.vars = ConfigVars()
        self.apc_queue = apc_queue
        self.gui_queue = gui_queue
        self.midimix_queue = midimix_queue
        self.ready_dispatch = self.on_ready
        self.event_dispatch = self.on_event
        self.ready = False
        self.shift = False
        self.midimix_shift = False
        self.display_view = 0
        self.channels_index = 0
        self.channelfxsend_index = 0
        self.last_used_channel = None
        self.master_lock = MASTER_LOCK
        self.master_lock_entry = []
        self.update_thread = Thread(
            target=self._update_thread,
            args=()
        )
        self.exit_flag = Event()

    def _update_thread(self) -> None:
        while not self.exit_flag.is_set():
            if self.apc_queue.qsize() == 0:
                continue
            msg = self.apc_queue.get()
            self.logger.info(f"APC => {msg}")
            if msg["key"] == "channel":
                if self.display_view != 0:
                    continue
                self.update_mix_channel(msg["data"]["channel"])
            elif msg["key"] == "master":
                if self.display_view != 7:
                    continue
                self.update_master_channel()
            elif msg["key"] == "fxmix":
                if self.display_view != 7:
                    continue
                self.update_fxreturn_channel(msg["data"]["channel"])
            elif msg["key"] == "init":
                self.display_mix_channels()
            elif msg["key"] == "shift":
                self.midimix_shift = msg["state"]
            else:
                if self.args.verbose:
                    self.logger.warning(f"{self.name} cant process \n{msg}")

    def join_thread(self) -> None:
        self.update_thread.join()

    def terminate(self) -> None:
        self.logger.warning(f"{self.name} => stopping")
        self.exit_flag.set()
        self.join_thread()

    def start(self) -> None:
        self.logger.critical(f"starting apc! state: {self.ready}")
        self.reset(fast=True)
        self.update_thread.start()

    def on_ready(self) -> None:
        self.ready = True

    def on_event(self, event) -> None:
        if isinstance(event, self.GridButton):
            if self.display_view not in [0, 7]:
                return None
            elif self.display_view == 0 and event.state:
                self.sender.mix(
                    event.x + self.channels_index,
                    self.vars.midi_grid_to_soundcraft(event.y),
                    "i"
                )
                self.last_used_channel = int(event.x)
            elif (
                self.display_view == 7
                and event.state
                and (self.shift or self.midimix_shift)
                and event.x in [4, 5, 6]
            ):
                if event.x == 4 and event.y == 7:
                    self.master_lock_entry = []
                    self.gridbuttons.set_led(4, 7, "red", "bright")
                    self.logger.warning("Master => lock => reset")
                    return None
                if self.master_lock_entry == self.master_lock:
                    return None
                if (event.x, event.y) \
                        == self.master_lock[len(self.master_lock_entry)]:
                    self.master_lock_entry.append((event.x, event.y))
                    if self.master_lock == self.master_lock_entry:
                        self.gridbuttons.set_led(4, 7, "green", "bright")
                        self.logger.warning("Master => lock => unlock")
                    return None
            elif (
                self.display_view == 7
                and event.state
                and self.master_lock_entry != self.master_lock
            ):
                self.logger.error("Master => lock => locked")
                return None
            elif (
                self.display_view == 7
                and event.state
                and event.x in range(4)
            ):
                self.sender.mix(
                    event.x,
                    self.vars.midi_grid_to_soundcraft(event.y),
                    "f"
                )
                self.last_used_channel = int(event.x)
            elif (
                self.display_view == 7
                and event.state
                and event.x == 7
            ):
                self.sender.master(self.vars.midi_grid_to_soundcraft(event.y))
                self.last_used_channel == int(event.x)
        elif isinstance(event, self.SideButton):
            if event.button_id == 0 and self.display_view != 0:
                self.display_view = 0
                self.last_used_channel = None
                self.display_mix_channels()
            elif event.button_id == 7 and self.display_view != 7:
                self.master_lock_entry = []
                self.display_view = 7
                self.last_used_channel = None
                self.display_master_fxreturn()
        elif isinstance(event, self.LowerButton):
            if not event.state:
                return None
            if (
                (self.shift or self.midimix_shift)
                and self.display_view == 0
                and event.button_id in [4, 5]
                and self.last_used_channel is not None
            ):
                value = float(
                    self.config.get_channel_value(
                        str(self.last_used_channel), "mix"
                    )
                )
                value += 0.002 if event.button_id == 4 else -0.002
                if event.button_id == 4 and value >= 1:
                    value = 1
                if event.button_id == 5 and value <= 0:
                    value = 0
                self.sender.mix(
                    self.last_used_channel,
                    value,
                    "i"
                )
                return None
            elif (
                (self.shift or self.midimix_shift)
                and self.display_view == 0
                and event.button_id == 6
                and self.check_index(self.channels_index - 1, 0, 4)
            ):
                self.channels_index -= 1
                self.display_mix_channels()
                self.gui_queue.put({
                    "key": "channel_move",
                    "data": {"inc": False, "index": self.channels_index}
                })
                return None
            elif (
                (self.shift or self.midimix_shift)
                and self.display_view == 0
                and event.button_id == 7
                and self.check_index(self.channels_index + 1, 0, 4)
            ):
                self.channels_index += 1
                self.display_mix_channels()
                self.gui_queue.put({
                    "key": "channel_move",
                    "data": {"inc": True, "index": self.channels_index}
                })
                return None
            elif (
                (self.shift or self.midimix_shift)
                and self.display_view == 7
                and self.last_used_channel is not None
                and event.button_id == 4
            ):
                if self.last_used_channel == 7:
                    next_value = float(self.config.get_master()) + 0.002
                    self.sender.master(
                        next_value if next_value <= 1 else 1
                    )
                else:
                    next_value = float(
                        self.config.get_fx_value(
                            str(self.last_used_channel), "mix"
                        )
                    ) + 0.002
                    self.sender.mix(
                        self.last_used_channel,
                        next_value if next_value <= 1 else 1
                    )
                return None
            elif (
                (self.shift or self.midimix_shift)
                and self.display_view == 7
                and self.last_used_channel is not None
                and event.button_id == 5
            ):
                if self.last_used_channel == 7:
                    next_value = float(self.config.get_master()) - 0.002
                    self.sender.master(
                        next_value if next_value >= 0 else 0
                    )
                else:
                    next_value = float(
                        self.config.get_fx_value(
                            str(self.last_used_channel), "mix"
                        )
                    ) - 0.002
                    self.sender.mix(
                        self.last_used_channel,
                        next_value if next_value >= 0 else 0
                    )
                return None
            elif (
                not self.shift and not self.midimix_shift
                and self.display_view == 0
            ):
                channel_id = event.button_id + self.channels_index
                self.logger.critical(f"{self.shift} && {self.midimix_shift}")
                self.logger.critical(
                    f"{self.config.get_channel_value(str(channel_id), 'mute')}"
                )
                mute_state = not bool(int(
                    self.config.get_channel_value(str(channel_id), "mute")
                ))
                self.sender.mute(
                    channel_id,
                    int(mute_state),
                    "i"
                )
                return None
            elif (
                not self.shift and not self.midimix_shift
                and self.display_view == 7
            ):
                pass
                # if event.button_id in range(4):
                #     self.sender.mix(
                #         event.button_id,
                #         0,
                #         "f"
                #     )
                #     return
                # if event.button_id == 7:
                #     self.sender.master(0)
        elif isinstance(event, self.Fader):
            if event.fader_id in list(range(5)):
                self.sender.fx_setting(
                    0,
                    event.fader_id + 1,
                    self.vars.midi_to_soundcraft(event.value)
                )
            elif event.fader_id in list(range(5, 9)):
                self.sender.fx_setting(
                    1,
                    (event.fader_id + 1) - 5,
                    self.vars.midi_to_soundcraft(event.value)
                )
        elif isinstance(event, self.ShiftButton):
            self.shift = True if event.state else False
            self.gui_queue.put({"key": "shift", "state": event.state})
            self.midimix_queue.put({"key": "shift", "state": event.state})

    def display_mix_channels(self) -> None:
        """ render full channel mix overview """
        self.reset(fast=True)
        self.set_view_button()
        for channel in range(
            self.channels_index,
            self.channels_index + 8
        ):
            self.update_mix_channel(channel)

    def update_mix_channel(self, channel: str | int) -> None:
        # Make sure channel value is type string
        # TODO: MAke sure channel is in view otherwise disregard information
        channel = str(channel)
        # Set values and request missing values from config
        if 0 > int(channel) - self.channels_index > 7:
            return None
        self.display_channel(
            int(channel) - self.channels_index,
            self.config.get_channel_value(channel, "mix"),
            "orange",
            self.config.get_channel_value(channel, "mute"),
            set_lower_as_zero=True
        )

    def display_master_fxreturn(self) -> None:
        self.reset(fast=True)
        self.set_view_button()
        self.update_master_channel()
        for fx in range(4):
            self.update_fxreturn_channel(fx)

    def update_master_channel(self) -> None:
        self.display_channel(
            7, self.config.get_master(),
            "red", 0, set_lower_as_zero=True
        )

    def update_fxreturn_channel(self, fx: int | str) -> None:
        self.display_channel(
            int(fx),
            self.config.get_fx_value(str(fx), "mix"),
            self.vars.map_color[int(fx)],
            self.config.get_fx_value(str(fx), "mute")
        )

    def set_view_button(self) -> None:
        """
            Set Sidebutton on if its the current view, else turn it off
        """
        for y in range(0, 8):
            self.sidebuttons.set_led(
                y,
                0 if y != self.display_view else 1
            )

    def display_channel(
            self, channel: int, value: str, colour: str,
            is_mute: str, set_lower_as_zero: bool = False
    ) -> None:
        mix_value = self.vars.soundcraft_to_midi(value)
        if 0 > int(channel):
            return None
        if int(channel) > 7:
            return None
        if mix_value == 0 and float(value) > 0:
            mix_value += 1
        elif mix_value == 8 and round(float(value), 1) < 1:
            mix_value -= 1
        for y in range(0, mix_value):
            self.gridbuttons.set_led(int(channel), y, colour, "bright")
        for y in range(mix_value, 8):
            self.gridbuttons.set_led(int(channel), y, "off", 0)
        if float(value) == 0 and set_lower_as_zero:
            self.lowerbuttons.set_led(int(channel), 2)
        if int(is_mute):
            self.lowerbuttons.set_led(int(channel), 1)
        if (
            not int(is_mute)
            and (
                float(value) > 0
                or (
                    float(value) == 0
                    and not set_lower_as_zero
                )
            )
        ):
            self.lowerbuttons.set_led(int(channel), 0)

    def is_alive(self) -> bool:
        return True if self.midi_string in get_output_names() else False

    def check_index(self, index, min, max) -> bool:
        """ Make sure the index vars do not reach out of bounce """
        return False if index < min or index > max else True
