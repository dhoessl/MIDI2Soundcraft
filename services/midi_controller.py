#!/home/dhoessl/midi_controller/bin/python3

from akai_pro_py import controllers
from time import sleep
from re import match
from mido import get_output_names


class APC(controllers.APCMinimkii):
    def __init__(self, midi_string, state, controller=None) -> None:
        super().__init__(midi_string, midi_string)
        self.midi_string = midi_string
        self.controller = controller
        self.ready_dispatch = self.on_ready
        self.event_dispatch = self.on_event
        self.mixer_is_connected = state
        self.ready = False
        self.shift = False

    def on_ready(self) -> None:
        print(f"{self.name}: Ready check in progress!")
        if self.mixer_is_connected:
            for x in range(8):
                self.lowerbuttons.set_led(x, 1)
                sleep(0.05)
            for x in range(8):
                self.lowerbuttons.set_led(x, 0)
                sleep(0.05)
        else:
            for x in range(1, 7):
                self.gridbuttons.set_led(x, x, "red", "bright")
                self.gridbuttons.set_led(x, 7-x, "red", "bright")
        self.ready = True
        print(f"{self.name}: Ready check completed!")

    def on_event(self, event) -> None:
        if not self.mixer_is_connected:
            print(f"{self.name}: Controller not connected - Abort event")
        if isinstance(event, self.GridButton):
            self.controller.apc_grid_event(event)
        elif isinstance(event, self.SideButton):
            self.controller.apc_side_event(event)
        elif isinstance(event, self.LowerButton):
            self.controller.apc_lower_event(event)
        elif isinstance(event, self.Fader):
            self.controller.apc_fader_event(event)
        elif isinstance(event, self.ShiftButton):
            if event.state:
                self.shift = True
            else:
                self.shift = False

    def is_alive(self) -> bool:
        if self.midi_string in get_output_names():
            return True
        else:
            return False

    def display_mix_channels(self) -> None:
        """ render full channel mix overview """
        self.reset(fast=True)
        self.set_view_button()
        for channel in range(self.controller.channels_index, self.controller.channels_index + 8):
            self.update_mix_channel(channel)

    def update_mix_channel(self, channel: int) -> None:
        while "mix" not in self.controller.channels[str(channel)]:
            continue
        config = self.controller.channels[str(channel)]
        self.display_channel(
            channel - self.controller.channels_index,
            config["mix"],
            "orange",
            config["mute"],
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
            7, self.controller.master,
            "red", 0, set_lower_as_zero=True
        )

    def update_fxreturn_channel(self, fx: int) -> None:
        self.display_channel(
            fx, self.controller.fx[str(fx)]["mix"],
            self.controller.get_fx_colour(fx),
            self.controller.fx[str(fx)]["mute"]
        )

    def set_view_button(self) -> None:
        """
            Set Sidebutton on if its the current view, else turn it off
        """
        for y in range(0, 8):
            self.sidebuttons.set_led(y, 0 if y != self.controller.display_view else 1)

    def display_channel(
            self, channel: int, value: str, colour: str,
            is_mute: str, set_lower_as_zero: bool = False
    ) -> None:
        mix_value = self.controller.soundcraft_to_midi(value)
        if mix_value == 0 and float(value) > 0:
            mix_value += 1
        elif mix_value == 8 and round(float(value), 1) < 1:
            mix_value -= 1
        for y in range(0, mix_value):
            self.gridbuttons.set_led(channel, y, colour, "bright")
        for y in range(mix_value, 8):
            self.gridbuttons.set_led(channel, y, "off", 0)
        self.lowerbuttons.set_led(channel, int(is_mute))
        if float(value) == 0 and set_lower_as_zero:
            self.lowerbuttons.set_led(channel, 2)


class Midimix(controllers.MIDIMix):
    def __init__(self, midi_string, state, controller=None) -> None:
        super().__init__(midi_string, midi_string)
        self.midi_string = midi_string
        self.controller = controller
        self.event_dispatch = self.on_event
        self.ready_dispatch = self.on_ready
        self.mixer_is_connected = state
        self.ready = False
        self.shift = False

    def on_ready(self) -> None:
        print(f"{self.name}: Ready check in progress!")
        if self.mixer_is_connected:
            for x in range(8):
                self.mutebuttons.set_led(x, 1)
                self.recarmbuttons.set_led(x, 1)
                sleep(0.05)
            for x in range(8):
                self.mutebuttons.set_led(x, 0)
                self.recarmbuttons.set_led(x, 0)
                sleep(0.05)
        else:
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
        self.ready = True
        print(f"{self.name}: Ready check completed!")

    def on_event(self, event) -> None:
        if not self.mixer_is_connected:
            print(f"{self.name}: Controller not connected - Abort event")
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
            if event.state:
                self.shift = True
            else:
                self.shift = False

    def is_alive(self) -> bool:
        if self.midi_string in get_output_names():
            return True
        else:
            return False


def get_midi_string(search) -> str:
    for port in get_output_names():
        matching = match(search, port)
        if matching:
            return matching.group()
    return None
