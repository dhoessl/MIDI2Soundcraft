from akai_pro_py import controllers
from soundcraft_ui16 import MixerSender
from logging import getLogger
from argparse import Namespace
from services.config import (
    Config, load_presets, remove_preset
)
from services.formatter import ConfigVars


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
        sender: MixerSender,
        config: Config,
        args: Namespace,
        logger_name: str = "Midimix",
        parent: None = None
    ) -> None:
        super().__init__(midi_string, midi_string)
        self.logger = getLogger(logger_name)
        self.args = args
        self.sender = sender
        self.config = config
        self.config_presets = load_presets()
        self.vars = ConfigVars()
        self.parent = parent
        self.event_dispatch = self.on_event
        self.ready_dispatch = self.on_ready
        self.ready = False
        self.shift = False
        self.apc_shift = False
        self.channelfxsend_index = 0

    def update_settings(self, msg) -> None:
        if msg["key"] == "init":
            self.reset()
            self.display_presets()
        elif msg["key"] == "apc_shift":
            self.apc_shift = msg["data"]["state"]
        else:
            if self.args.verbose:
                self.logger.warning(f"{self.name} cant process\n{msg}")

    def on_ready(self) -> None:
        self.ready = True
        self.logger.warning(f"{self.name} is ready!")

    def on_event(self, event) -> None:
        if isinstance(event, self.Knob):
            current_knob = (event.x, event.y)
            for check_set in self.KNOB_MAPPING:
                if current_knob in check_set:
                    channel = self.KNOB_MAPPING.index(check_set)
                    break
            channel_send = channel + self.channelfxsend_index * 6
            self.sender.fx(
                channel_send,
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
                self.mutebuttons.set_led(event.button_id, 1)
            elif (
                (self.shift or self.apc_shift)
                and str(event.button_id) in self.config_presets
            ):
                # Delete a preset
                remove_preset(str(event.button_id))
                self.config_presets = load_presets()
                self.mutebuttons.set_led(event.button_id, 0)
            else:
                # Do nothing no preset is set here
                pass
        if isinstance(event, self.RecArmButton):
            if not event.state:
                return None
            if (
                not self.shift and not self.apc_shift
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
                not self.shift and not self.apc_shift
                and str(event.button_id + 8) not in self.config_presets
            ):
                # Save config as preset
                self.config.create_preset(str(event.button_id + 8))
                self.config_presets = load_presets()
                self.recarmbuttons.set_led(event.button_id, 1)
            elif (
                (self.shift or self.apc_shift)
                and str(event.button_id + 8) in self.config_presets
            ):
                # Delete a preset
                remove_preset(str(event.button_id + 8))
                self.config_presets = load_presets()
                self.recarmbuttons.set_led(event.button_id, 0)
            else:
                # Do nothing no preset is set here
                pass
        if isinstance(event, self.BankButton):
            if event.state and event.button_id and self.channelfxsend_index:
                self.channelfxsend_index = 0
                self.parent.notify_update("fx_move")
            if (event.state and not event.button_id
                    and not self.channelfxsend_index):
                self.channelfxsend_index = 1
                self.parent.notify_update("fx_move")
        if isinstance(event, self.SoloButton):
            self.shift = True if event.state else False
            self.parent.notify_update(
                "midimix_shift",
                {"state": event.state}
            )

    def display_presets(self) -> None:
        for preset in self.config_presets:
            if int(preset) < 8:
                self.mutebuttons.set_led(int(preset), 1)
            else:
                self.recarmbuttons.set_led(int(preset) - 8, 1)
