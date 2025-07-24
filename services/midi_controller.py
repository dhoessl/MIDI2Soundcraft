#!/home/dhoessl/midi_controller/bin/python3

from akai_pro_py import controllers
from time import sleep
from re import match
from mido import get_output_names
from colorama import Fore
from logging import getLogger, INFO
from .formatter import ConfigVars


class APC(controllers.APCMinimkii):
    def __init__(
            self, midi_string: str,
            state: bool, controller=None,
            logname: str = "APC"
    ) -> None:
        super().__init__(midi_string, midi_string)
        self.logger = getLogger(logname)
        if self.logger.level < 20:
            self.logger.setLevel(INFO)
        self.midi_string = midi_string
        self.controller = controller
        self.ready_dispatch = self.on_ready
        self.event_dispatch = self.on_event
        self.mixer_is_connected = state
        self.ready = False
        self.shift = False
        self.vars = ConfigVars()

    def on_ready(self) -> None:
        self.logger.warning(f"{self.name} Ready Check")
        if not self.mixer_is_connected:
            for x in range(1, 7):
                self.gridbuttons.set_led(x, x, "red", "bright")
                self.gridbuttons.set_led(x, 7-x, "red", "bright")
                self.logger.critical(f"{self.name} <> Mixer not connected")
        self.ready = True
        self.logger.info(f"{Fore.GREEN}{self.name} Ready Check completed!")

    def on_event(self, event) -> None:
        if not self.mixer_is_connected:
            self.logger.error(f"{self.name} -> Not connected - Abort Event")
        if isinstance(event, self.GridButton):
            self.controller.apc_grid_event(event)
        elif isinstance(event, self.SideButton):
            self.controller.apc_side_event(event)
        elif isinstance(event, self.LowerButton):
            self.controller.apc_lower_event(event)
        elif isinstance(event, self.Fader):
            self.controller.apc_fader_event(event)
        elif isinstance(event, self.ShiftButton):
            self.shift = True if event.state else False

    def is_alive(self) -> bool:
        return True if self.midi_string in get_output_names() else False

    def display_mix_channels(self) -> None:
        """ render full channel mix overview """
        self.reset(fast=True)
        self.set_view_button()
        for channel in range(
            self.controller.channels_index,
            self.controller.channels_index + 8
        ):
            self.update_mix_channel(channel)

    def update_mix_channel(self, channel: str | int) -> None:
        # Make sure channel value is type string
        channel = str(channel)
        # Set values and request missing values from config
        self.display_channel(
            int(channel) - self.controller.channels_index,
            self.controller.config.get_channel_value(channel, "mix"),
            "orange",
            self.controller.config.get_channel_value(channel, "mute"),
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
            7, self.controller.config.get_master(),
            "red", 0, set_lower_as_zero=True
        )

    def update_fxreturn_channel(self, fx: int | str) -> None:
        self.display_channel(
            int(fx),
            self.controller.config.get_fx_value(str(fx), "mix"),
            self.vars.map_color[int(fx)],
            self.controller.config.get_fx_value(str(fx), "mute")
        )

    def set_view_button(self) -> None:
        """
            Set Sidebutton on if its the current view, else turn it off
        """
        for y in range(0, 8):
            self.sidebuttons.set_led(
                y,
                0 if y != self.controller.display_view else 1
            )

    def display_channel(
            self, channel: int, value: str, colour: str,
            is_mute: str, set_lower_as_zero: bool = False
    ) -> None:
        mix_value = self.vars.soundcraft_to_midi(value)
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


class Midimix(controllers.MIDIMix):
    def __init__(
            self, midi_string: str,
            state: bool, controller=None,
            logname: str = "MidiMix"
    ) -> None:
        super().__init__(midi_string, midi_string)
        self.logger = getLogger(logname)
        if self.logger.level < 20:
            self.logger.setLevel(INFO)
        self.midi_string = midi_string
        self.controller = controller
        self.event_dispatch = self.on_event
        self.ready_dispatch = self.on_ready
        self.mixer_is_connected = state
        self.ready = False
        self.shift = False
        self.vars = ConfigVars()

    def on_ready(self) -> None:
        self.logger.warning(f"{self.name} Ready Check")
        if not self.mixer_is_connected:
            counter = 0
            while self.is_alive() and counter in range(20):
                for x in range(8):
                    self.mutebuttons.set_led(x, 1)
                    self.recarmbuttons.set_led(x, 1)
                sleep(0.2)
                for x in range(8):
                    self.mutebuttons.set_led(x, 0)
                    self.recarmbuttons.set_led(x, 0)
                sleep(0.2)
                counter += 1
            self.logger.critical(f"{self.name} Mixer not connected")
        self.ready = True
        self.logger.info(f"{Fore.GREEN}{self.name} Ready Check completed!")
        for preset in self.controller.config_presets:
            if preset < 8:
                self.mutebuttons.set_led(preset, 1)
            else:
                self.recarmbuttons.set_led(preset - 8, 1)

    def on_event(self, event) -> None:
        if not self.mixer_is_connected:
            self.logger.error(f"{self.name} -> Not connected - Abort Event")
        if isinstance(event, self.Knob):
            self.controller.midi_mix_knob_event(event)
        if isinstance(event, self.Fader):
            self.controller.midi_mix_fader_event(event)
        if isinstance(event, self.MuteButton):
            self.controller.midi_mix_mute_event(event)
        if isinstance(event, self.RecArmButton):
            self.controller.midi_mix_recarm_event(event)
        if isinstance(event, self.BankButton):
            self.controller.midi_mix_bank_event(event)
        if isinstance(event, self.SoloButton):
            # Solobutton is MIDI Mix Shift button
            self.shift = True if event.state else False

    def is_alive(self) -> bool:
        return True if self.midi_string in get_output_names() else False


def get_midi_string(search) -> str:
    for port in get_output_names():
        matching = match(search, port)
        if matching:
            return matching.group()
    return None
