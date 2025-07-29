from .formatter import ConfigVars, OutputFormatter
from .gui import BaseFrame
from .config import Config
from logging import getLogger


class GuiController:
    def __init__(
        self,
        gui: BaseFrame,
        config: Config,
        logger_name: str = "GuiController",
        parent: None = None
    ) -> None:
        self.logger = getLogger(logger_name)
        self.gui = gui
        self.vars = ConfigVars()
        self.config = config
        self.formatter = OutputFormatter()
        self.parent = parent

    def update_settings(self, msg) -> None:
        if msg["key"] == "bpm":
            self.update_bpm()
        elif msg["key"] == "channel_fx":
            self.update_channel_fx(
                msg["data"]["channel"],
                msg["data"]["fx"],
                msg["data"]["function"]
            )
        elif msg["key"] == "channel":
            self.update_apc_mix_channel(msg["data"]["channel"])
        elif msg["key"] == "master":
            self.update_master()
        elif msg["key"] == "fxmix":
            self.update_fx_return(msg["data"]["channel"])
        elif msg["key"] == "fxpar":
            self.update_fx_params(
                msg["data"]["channel"],
                msg["data"]["function"]
            )
        elif msg["key"] == "channel_move":
            self.update_mix_channels(
                msg["data"]["inc"],
                msg["data"]["index"]
            )
        elif msg["key"] == "fx_move":
            self.update_dial_channels()
        elif msg["key"] == "apc_shift":
            self.set_shift_button(msg["data"]["state"], "apc")
        elif msg["key"] == "midimix_shift":
            self.set_shift_button(msg["data"]["state"], "midimix")
        elif msg["key"] == "matrix_view":
            self.set_apc_side_button(msg["data"]["view"])
        else:
            pass  # since no logger is active here

    def update_bpm(self) -> None:
        bpm = int(self.config.get_bpm())
        self.gui.change_midimix_slider_value(
            8, bpm, f"{bpm}"
        )

    def update_master(self) -> None:
        master = float(self.config.get_master())
        self.gui.set_apc_channel_value(
            7, self.vars.soundcraft_to_midi(master),
            self.formatter.mix(master)
        )

    def update_channel_fx(
        self,
        channel: str | int,
        fx: str | int,
        key: str | int
    ) -> None:
        if key != "value":
            return None
        value = float(self.config.get_channel_fx_value(channel, fx, key))
        self.gui.change_dial_value(
            int(channel), int(fx),
            int(round(float(self.vars.soundcraft127(value)), 0)),
            self.formatter.mix(value)
        )

    def update_apc_mix_channel(self, channel: str | int) -> None:
        value_mix = float(self.config.get_channel_value(channel, "mix"))
        value_mute = int(self.config.get_channel_value(channel, "mute"))
        self.gui.set_apc_channel_value(
            int(channel), self.vars.soundcraft_to_midi(value_mix),
            self.formatter.mix(value_mix)
        )
        self.gui.set_apc_mute_button(int(channel), value_mute)

    def update_fx_return(self, channel: str | int) -> None:
        value = float(self.config.get_fx_value(channel, "mix"))
        self.gui.set_apc_channel_value(
            int(channel), self.vars.soundcraft_to_midi(value),
            self.formatter.mix(value)
        )

    def set_shift_button(self, state: bool) -> None:
        self.gui.set_shift_button(state)

    def update_fx_params(self, channel: str | int, key: str) -> None:
        try:
            delay_time = float(self.config.get_fx_value("1", "par1"))
        except:  # noqa: E722
            delay_time = 1
        try:
            value = float(self.config.get_fx_value(channel, key))
            value_slider = round(float(self.vars.soundcraft127(value)), 0)
            value_text = self.formatter.fx_parval(
                channel, key, value, delay_time
            )
        except TypeError:
            # Update Thread is sending notifications for
            # non existing parameters since they just get
            # filtered on config level
            # TODO: create filter for notifications too
            return None
        if int(channel) == 0:
            self.gui.change_apc_slider_value(
                int(key[-1:]) - 1,
                value_slider, value_text
            )
        elif int(channel) == 1:
            self.gui.change_apc_slider_value(
                int(key[-1:]) + 4,
                value_slider, value_text
            )
        elif int(channel) == 2:
            self.gui.change_midimix_slider_value(
                int(key[-1:]) - 1,
                value_slider, value_text
            )
        elif int(channel) == 3:
            self.gui.change_midimix_slider_value(
                int(key[-1:]) + 2,
                value_slider, value_text
            )

    def update_mix_channels(self, increment: bool, index: int) -> None:
        data = {}
        for channel in range(12):
            value_mix = float(
                self.config.get_channel_value(str(channel), "mix")
            )
            data[channel] = {
                "btns": self.vars.soundcraft_to_midi(value_mix),
                "value": self.formatter.mix(value_mix),
            }
        self.gui.change_apc_channels(increment, data)
        for lower_button in range(index, 8 + index):
            mute_values = []
            mute_values.append(
                int(self.config.get_channel_value(str(lower_button), "mute"))
            )
        for val in mute_values:
            self.gui.set_apc_mute_button(mute_values.index(val), bool(val))

    def update_dial_channels(self) -> None:
        data = {}
        for channel in range(12):
            data[channel] = {}
            for fx in range(4):
                value = float(self.config.get_channel_fx_value(
                    str(channel), str(fx), "value"
                ))
                data[channel][fx] = {
                    "value": round(float(self.vars.soundcraft127(value)), 0),
                    "label": self.formatter.mix(value)
                }
        self.gui.change_dial_channels(data)
