from .formatter import OutputFormatter, ConfigVars
from logging import getLogger
from os import path
from pathlib import Path
from json import dumps, loads

MIXER_ADDRESS = "10.10.1.1"
MIXER_PORT = 80

MIDI_CONTROLLER = {
    "APC": {
        "name": "APC",
        "discovery": r"^APC mini mk2.*?Contr.*?$"
    },
    "MIDIMIX": {
        "name": "MidiMix",
        "discovery": r"^MIDI Mix.*?$"
    }
}

MASTER_LOCK = [(4, 0), (5, 0), (6, 0), (6, 7)]
PRESET_FILE = path.expanduser("~/.config/midi2soundcraft_presets.json")


def load_presets() -> dict:
    """ Reads the presets config file.
        If the files does not exist it will be created
    """
    if not path.exists(PRESET_FILE):
        Path(PRESET_FILE).touch()
        with open(PRESET_FILE, "w") as fp:
            fp.write(dumps({}))
    with open(PRESET_FILE, "r") as fp:
        config = loads(fp.read())
    return config


def remove_preset(preset_id) -> None:
    """ List presets. Remove preset with preset_id as key.
        Write changes to preset file.
    """
    with open(PRESET_FILE, "r") as fp:
        config = loads(fp.read())
    del config[preset_id]
    with open(PRESET_FILE, "w") as fp:
        fp.write(dumps(config))


class Config:
    def __init__(self, logger_name: str = "ConfigObject") -> None:
        self.logger = getLogger(logger_name)
        self.master = None
        self.bpm = None
        self.channels = ChannelCollection()
        self.fx = FxCollection()
        self.vars = ConfigVars()
        self.formatter = OutputFormatter()

    def update_master(self, value) -> None:
        self.master = value
        self.logger.warning(f"MASTER => {self.formatter.mix(self.master)}")

    def get_master(self) -> str:
        return self.master

    def update_bpm(self, value) -> None:
        self.bpm = value
        self.logger.info(f"BPM => {self.bpm}")

    def get_bpm(self) -> str:
        return self.bpm

    def update_fx(self, fx_id, key, value) -> None:
        self.fx.update(fx_id, key, value)
        # send fx1 par1 parameter to set delay mode correctly
        fx1par1 = 1
        if int(fx_id) == 1 and key == "par2":
            fx1par1 = self.get_fx_value("1", "par1")
            fx1par1 = float(fx1par1) if fx1par1 else 1
        self.logger.info(
            f"{self.formatter.fx_name(fx_id)} => "
            f"{self.formatter.fx_parname(fx_id, key)} => "
            f"{self.formatter.fx_parval(fx_id, key, value, fx1par1)}"
        )

    def get_fx_value(self, fx_id, value) -> str:
        return self.fx.get_value(fx_id, value)

    def update_channel(self, channel_id, key, value) -> None:
        self.channels.update(channel_id, key, value)
        if key == "mix" or key == "gain":
            return_value = self.formatter.mix(value)
        if key == "mute" or key == "solo":
            return_value = False if int(value) == 0 else True
        self.logger.info(
            f"Channel {channel_id} => {key} => {return_value}"
        )

    def get_channel_value(self, channel_id, value) -> str:
        return self.channels.get_value(channel_id, value)

    def update_channel_fx(self, channel_id, fx_id, key, value) -> None:
        self.channels.update_fx(channel_id, fx_id, key, value)
        self.logger.info(
            f"Channel {channel_id} => "
            f"{self.formatter.fx_name(fx_id)} => {self.formatter.mix(value)}"
        )

    def get_channel_fx_value(self, channel_id, fx_id, value) -> str:
        return self.channels.get_fx_value(channel_id, fx_id, value)

    def create_preset(self, button) -> dict:
        preset = {
            "fx": self.fx.create_preset()
        }
        # Read more values if you want to save more in a preset
        self.save_preset(button, preset)
        return preset

    def save_preset(self, button, preset) -> None:
        config = {}
        if path.exists(PRESET_FILE):
            # Read existing config
            with open(PRESET_FILE, "r") as fp:
                config = loads(fp.read())
        else:
            # Make sure file exists to not create Permission Errors
            Path(PRESET_FILE).touch()
        # Merge config
        config[button] = preset
        with open(PRESET_FILE, "w") as fp:
            fp.write(dumps(config))


class Fx:
    def __init__(self, fx_id) -> None:
        self.id = fx_id
        self.functions = {}

    def update(self, key, value) -> None:
        if self.id == "0" and key == "par6":
            # this par does not exist
            return None
        if self.id == "3" and key == "par6":
            # this par does not exist
            return None
        if self.id == "1" and (key == "par5" or key == "par6"):
            # these par does not exist for this fx
            return None
        if self.id == "2" and (
            key == "par4"
            or key == "par5"
            or key == "par6"
        ):
            # These keys do not exist either
            return None
        self.functions[key] = value

    def get_value(self, key) -> str:
        if key not in self.functions:
            return None
        else:
            return self.functions[key]


class FxCollection:
    def __init__(self) -> None:
        self.fx = self.create_fxs()

    def update(self, fx_id, key, value) -> None:
        update_fx = self.get_fx(fx_id)
        update_fx.update(key, value)

    def get_value(self, fx_id, key) -> None:
        request_fx = self.get_fx(fx_id)
        return request_fx.get_value(key)

    def create_fxs(self) -> list:
        return [Fx("0"), Fx("1"), Fx("2"), Fx("3")]

    def get_fx(self, fx_id) -> Fx:
        for fx in self.fx:
            if fx.id == fx_id:
                return fx
        return None

    def create_preset(self) -> dict:
        fx_values = {}
        for fx in self.fx:
            fx_values[fx.id] = fx.functions
        return fx_values


class Channel:
    def __init__(self, channel_id) -> None:
        self.id = channel_id
        self.fx = FxCollection()
        self.functions = {}

    def update_fx(self, fx_id, key, value) -> None:
        self.fx.update(fx_id, key, value)

    def update(self, key, value) -> None:
        self.functions[key] = value

    def get_fx_value(self, fx_id, key) -> str:
        return self.fx.get_value(fx_id, key)

    def get_value(self, key) -> str:
        if key not in self.functions:
            return None
        return self.functions[key]


class ChannelCollection:
    def __init__(self) -> None:
        self.channels = []

    def create_channel(self, channel_id) -> None:
        """ Create a channel with a given id """
        created_channel = Channel(channel_id)
        self.channels.append(created_channel)
        return created_channel

    def update_fx(self, channel_id, fx_id, key, value) -> None:
        """ Update a fx value of a channel """
        channel = self.get_channel(channel_id)
        channel.update_fx(fx_id, key, value)

    def update(self, channel_id, key, value) -> None:
        channel = self.get_channel(channel_id)
        channel.update(key, value)

    def get_fx_value(self, channel_id, fx_id, key) -> str:
        channel = self.get_channel(channel_id)
        return channel.get_fx_value(fx_id, key)

    def get_value(self, channel_id, key) -> str:
        channel = self.get_channel(channel_id)
        return channel.get_value(key)

    def get_channel(self, channel_id) -> Channel:
        """ Search for the specific Channel inside self.channels
            If the channel does not exist create a new one
        """
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return self.create_channel(channel_id)
