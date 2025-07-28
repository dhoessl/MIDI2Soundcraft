from akai_pro_py import controllers
from soundcraft_ui16 import MixerSender
from mido import get_output_names
from time import sleep
from re import match
from logging import getLogger
from threading import Thread, Event
from queue import Queue
from argparse import Namespace
from services.config import (
    MIDIMIX_DISCOVER_STRING, Config, load_presets, remove_preset
)
from services.formatter import ConfigVars


class MidimixControllerThread:
    def __init__(
        self,
        midimix_queue: Queue,
        gui_queue: Queue,
        apc_queue: Queue,
        sender: MixerSender,
        config: Config,
        args: Namespace,
        logger_name: str = "MidiMix"
    ) -> None:
        self.logger = getLogger(logger_name)
        self.args = args
        self.midi_string = self.get_midi_string(MIDIMIX_DISCOVER_STRING)
        self.sender = sender
        self.midimix_queue = midimix_queue
        self.gui_queue = gui_queue
        self.config = config
        self.midimix = None
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
                self.logger.warning("No Port for Midimix found")
                self.midi_string = \
                    self.get_midi_string(MIDIMIX_DISCOVER_STRING)
                sleep(.5)
                continue
            if (
                not self.midimix
                or (
                    self.midimix
                    and self.midimix.ready
                    and self.midimix.is_alive()
                )
            ):
                if self.midimix:
                    self.midimix.terminate()
                try:
                    self.midimix = Midimix(
                        self.midi_string, self.midimix_queue,
                        self.gui_queue, self.sender,
                        self.config, self.args, self.logger.name
                    )
                    # Drain Queue and send init request
                    while self.midimix_queue.qsize() > 0:
                        self.midimix_queue.get()
                    self.midimix_queue.put({"key": "init"})
                    self.logger.warning(f"{self.midimix.name} => created!")
                except:  # noqa: E722
                    self.logger.critical("Midimix => failed!")

    def start(self) -> None:
        self.keepalive_thread.start()

    def join(self) -> None:
        self.keepalive_thread.join()

    def terminate(self) -> None:
        self.exit_flag.set()
        self.join()


class Midimix(controllers.MIDIMix):
    KNOB_MAPPING = [
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(4, 2), (5, 2), (6, 2), (7, 2)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(4, 1), (5, 1), (6, 1), (7, 1)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(4, 0), (5, 0), (6, 0), (7, 0)]
    ]

    def __init__(
        self,
        midi_string: str,
        midimix_queue: Queue,
        gui_queue: Queue,
        sender: MixerSender,
        config: Config,
        args: Namespace,
        logger_name: str = "Midimix"
    ) -> None:
        super().__init__(midi_string, midi_string)
        self.midi_string = midi_string
        self.args = args
        self.logger = getLogger(logger_name)
        self.sender = sender
        self.config = config
        self.config_presets = load_presets()
        self.vars = ConfigVars()
        self.midimix_queue = midimix_queue
        self.gui_queue = gui_queue
        self.event_dispatch = self.on_event
        self.ready_dispatch = self.on_ready
        self.ready = False
        self.shift = False
        self.apc_shift = False
        self.channelfxsend_index = 0
        self.update_thread = Thread(
            target=self._update_thread,
            args=()
        )
        self.exit_flag = Event()

    def _update_therad(self) -> None:
        while not self.exit_flag.is_set():
            if self.midimix_queue.qsize() == 0:
                continue
            msg = self.apc_queue.get()
            if msg["key"] == "init":
                self.display_presets()
            elif msg["key"] == "shift":
                self.apc_shift = msg["state"]
            else:
                if self.args.verbose:
                    self.logger.warning(f"{self.name} cant process \n{msg}")

    def join_thread(self) -> None:
        self.update_thread.join()

    def terminate(self) -> None:
        self.exit_flag.set()
        self.join_thread()

    def on_ready(self) -> None:
        self.ready = True
        self.update_thread.start()
        self.logger.warning(f"{self.name} is ready!")

    def on_event(self, event) -> None:
        if isinstance(event, self.Knob):
            current_knob = (event.x, event.y)
            for check_set in self.KNOB_MAPPING:
                if current_knob in check_set:
                    channel = self.KNOB_MAPPING.index(check_set)
                    break
            channel += self.channelfxsend_index * 6
            self.sender.fx(
                channel,
                self.vars.midi_to_soundcraft(event.value),
                "i", self.KNOB_MAPPING[channel].index((event.x, event.y))
            )
        if isinstance(event, self.Fader):
            if event.fader_id in list(range(3)):
                self.sender.fx_setting(
                    2,
                    event.fader_id + 1,
                    self.vars.midi_to_soundcraft(event.value)
                )
            elif event.fader_id in list(range(3, 8)):
                self.sender.fx_setting(
                    3,
                    (event.fader_id + 1) - 3,
                    self.vars.midi_to_soundcraft(event.value)
                )
            elif event.fader_id == 8:
                # Set the BPM - Values will be 60 to 60 + range(128)  = 187
                self.sender.tempo(
                    60 + event.value
                )
        if isinstance(event, self.MuteButton):
            if not event.state:
                return None
            if (
                not self.shift and not self.apc_shift
                and str(event.button_id) in self.config_presets
            ):
                # Load Config
                effects = self.config_presets[str(event.button_id)]["fx"]
                for fx in effects:
                    for option in effects[fx]:
                        if "par" not in option:
                            continue
                        self.sender.fx_setting(
                            int(fx),
                            int(option[-1:]),
                            float(effects[fx][option])
                        )
            elif (
                not self.shift and not self.apc_shift
                and str(event.button_id) not in self.config_presets
            ):
                # Save config as preset
                self.config.create_preset(str(event.button_id))
                self.config_presets = load_presets()
                self.midimix.mutebuttons.set_led(event.button_id, 1)
            elif (
                (self.shift or self.apc_shift)
                and str(event.button_id) in self.config_presets
            ):
                # Delete a preset
                remove_preset(str(event.button_id))
                self.config_presets = load_presets()
                self.midimix.mutebuttons.set_led(event.button_id, 0)
            else:
                # Do nothing no preset is set here
                pass
        if isinstance(event, self.RecArmButton):
            if not event.state:
                return None
            if (
                not self.shift and not self.midimix_shift
                and str(event.button_id + 8) in self.config_presets
            ):
                # Load Config
                effects = self.config_presets[str(event.button_id + 8)]["fx"]
                for fx in effects:
                    for option in effects[fx]:
                        if "par" not in option:
                            continue
                        self.sender.fx_setting(
                            int(fx),
                            int(option[-1:]),
                            float(effects[fx][option])
                        )
            elif (
                not self.shift and not self.midimix_shift
                and str(event.button_id + 8) not in self.config_presets
            ):
                # Save config as preset
                self.config.create_preset(str(event.button_id + 8))
                self.config_presets = load_presets()
                self.midimix.recarmbuttons.set_led(event.button_id, 1)
            elif (
                (self.shift or self.apc_shift)
                and str(event.button_id + 8) in self.config_presets
            ):
                # Delete a preset
                remove_preset(str(event.button_id + 8))
                self.config_presets = load_presets()
                self.midimix.recarmbuttons.set_led(event.button_id, 0)
            else:
                # Do nothing no preset is set here
                pass
        if isinstance(event, self.BankButton):
            if event.state and event.button_id and self.channelfxsend_index:
                self.channelfxsend_index = 0
                self.gui_queue.put({"key": "fx_move"})
            if (event.state and not event.button_id
                    and not self.channelfxsend_index):
                self.channelfxsend_index = 1
                self.gui_queue.put({"key": "fx_move"})
        if isinstance(event, self.SoloButton):
            self.shift = True if event.state else False
            self.apc_queue.put({"key": "shift", "state": event.state})
            self.gui_queue.put({"key": "shift", "state": event.state})

    def display_presets(self) -> None:
        for preset in self.config_presets:
            if preset < 8:
                self.midimix.mutebuttons.set_led(int(preset), 1)
            else:
                self.midimix.recarmbuttons.set_led(int(preset) - 8, 1)

    def is_alive(self) -> bool:
        return True if self.midi_string in get_output_names() else False
