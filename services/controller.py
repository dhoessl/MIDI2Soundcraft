from soundcraft_ui16 import MixerListener, MixerSender
from lcd_i2c_display_matrix.lcd_websocket_sender import MatrixCommandSender
from .midi_controller import APC, Midimix, get_midi_string
from queue import Queue
from threading import Thread, Event
from time import sleep
from re import match
from scipy.interpolate import interp1d


class Controller:
    KNOB_MAPPING = [
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(4, 2), (5, 2), (6, 2), (7, 2)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(4, 1), (5, 1), (6, 1), (7, 1)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(4, 0), (5, 0), (6, 0), (7, 0)]
    ]
    MIX_STD50 = interp1d([0.527044025, 1], [-10, 10])
    MIX_STD37 = interp1d([0.372327044, 0.527044025], [-20, -10])
    MIX_STD18 = interp1d([0.181132075, 0.372327044], [-40, -20])
    MIX_STD5 = interp1d([0.056603773, 0.181132075], [-60, -40])
    MIX_STD0 = interp1d([0, 0.181132075], [-90, -60])
    MAP_100 = interp1d([0, 1], [0, 100])
    MAP_200 = interp1d([0, 1], [0, 200])
    MAP_100pm = interp1d([0, 1], [-100, 100])
    MAP_LPF_REV = [
        interp1d([0, .1], [400, 597]),
        interp1d([.1, .2], [597, 891]),
        interp1d([.2, .3], [891, 1330]),
        interp1d([.3, .4], [1330, 1980]),
        interp1d([.4, .5], [1980, 2960]),
        interp1d([.5, .6], [2960, 4430]),
        interp1d([.6, .7], [4430, 6620]),
        interp1d([.7, .8], [6620, 9890]),
        interp1d([.8, .9], [9890, 14700]),
        interp1d([.9, 1], [14700, 22000]),
    ]
    MAP_TIME_REV = [
        interp1d([0, .1], [300, 416]),
        interp1d([.1, .2], [416, 578]),
        interp1d([.2, .3], [578, 803]),
        interp1d([.3, .4], [803, 1115]),
        interp1d([.4, .5], [1115, 1549]),
        interp1d([.5, .6], [1549, 2151]),
        interp1d([.6, .7], [2151, 2987]),
        interp1d([.7, .8], [2987, 4148]),
        interp1d([.8, .9], [4148, 5760]),
        interp1d([.9, 1], [5760, 8000])
    ]
    MAP_HPF_REV = [
        interp1d([0, .1], [20, 34]),
        interp1d([.1, .2], [34, 60]),
        interp1d([.2, .3], [60, 104]),
        interp1d([.3, .4], [104, 182]),
        interp1d([.4, .5], [182, 316]),
        interp1d([.5, .6], [316, 549]),
        interp1d([.6, .7], [549, 954]),
        interp1d([.7, .8], [954, 1650]),
        interp1d([.8, .9], [1650, 2870]),
        interp1d([.9, 1], [2870, 5000])
    ]
    MAP_TIME_DELAY = [
        interp1d([0, .1], [0, 154]),
        interp1d([.1, .2], [154, 229]),
        interp1d([.2, .3], [229, 323]),
        interp1d([.3, .4], [323, 436]),
        interp1d([.4, .5], [436, 562]),
        interp1d([.5, .6], [562, 691]),
        interp1d([.6, .7], [691, 812]),
        interp1d([.7, .8], [812, 912]),
        interp1d([.8, .9], [912, 977]),
        interp1d([.9, 1], [977, 1000])
    ]
    MAP_LPF_DELAY = [
        interp1d([0, .1], [20, 40]),
        interp1d([.1, .2], [40, 81]),
        interp1d([.2, .3], [81, 163]),
        interp1d([.3, .4], [163, 329]),
        interp1d([.4, .5], [329, 664]),
        interp1d([.5, .6], [664, 1330]),
        interp1d([.6, .7], [1330, 2690]),
        interp1d([.7, .8], [2690, 5430]),
        interp1d([.8, .9], [5430, 10900]),
        interp1d([.9, 1], [10900, 22000]),
    ]
    MAP_TIME_ROOM = [
        interp1d([0, .1], [100, 125]),
        interp1d([.1, .2], [125, 158]),
        interp1d([.2, .3], [158, 199]),
        interp1d([.3, .4], [199, 251]),
        interp1d([.4, .5], [251, 316]),
        interp1d([.5, .6], [316, 398]),
        interp1d([.6, .7], [398, 501]),
        interp1d([.7, .8], [501, 630]),
        interp1d([.8, .9], [630, 794]),
        interp1d([.9, 1], [794, 1000]),
    ]

    def __init__(self, mixer_addr, lcd_addr):
        """ Brain of the connection between APC mini mk2 and Soundcraft UI16
            self.apc is the connection to the APC mini mk2.
            self.listener and self.sender are the connection to the Soundcraft
        """
        self.mixer_addr = mixer_addr
        self.lcd_addr = lcd_addr
        self.apc = None
        self.midi_mix = None
        self.apc_discovery_string = r"^APC mini mk2.*?Contr.*?$"
        self.midimix_discovery_string = r"^MIDI Mix.*?$"

        # # Soundcraft Control
        self.msg_bus = Queue()
        # Setup sender connection
        self.sender = MixerSender(mixer_addr, 80)
        self.listener = MixerListener(mixer_addr, 80, queue=self.msg_bus)
        # Start the listener and sender
        self.listener.start()
        self.sender.start()

        # Threading
        # Create Thread to show updates in real time on the APC mini mk2
        self.update_thread = Thread(
            target=self.update_config_thread,
            args=()
        )
        self.update_exit = Event()
        self.midi_keepalive_thread = Thread(
            target=self.midi_keepalive,
            args=()
        )
        self.midi_keepalive_exit = Event()

        # # Settings
        # Values to store the Soundcraft Ui16 state
        # Update by the self.update_thread Thread
        self.channels = {}
        self.master = 0
        self.fx = {}

        # # APC vars
        # Some vars to display the correct
        # values on the APC mini mk2
        self.display_view = 0
        self.channels_index = 0
        self.channelfxsend_index = 0
        self.apc_last_used_channel = None
        self.apc_master_lock = [(4, 0), (5, 0), (6, 0), (6, 7)]
        self.apc_master_lock_entry = []

        # LCD Matrix Sender
        self.lcdsender = MatrixCommandSender(lcd_addr, 80)

    def run(self) -> None:
        """
            Function to start and keep the Controller class alive
            The Controller will start an instance of the apc and midimx
        """
        counter = 0
        while not self.listener.connected:
            self.lcdsender.send(
                "on_next_or_id",
                ["INFO: Mixer", f"waiting {counter}"],
                "mixer_status"
            )
            counter += 1
            sleep(.5)
        self.lcdsender.send(
            "on_next_or_id",
            ["INFO: Mixer", "Connected!"],
            "mixer_status"
        )
        # Load the listener again if no data was received
        while self.msg_bus.qsize() < 1:
            self.listener = MixerListener(
                self.mixer_addr, 80,
                queue=self.msg_bus
            )
            sleep(.3)
        # start the config updates
        self.update_thread.start()
        # Wait for the initial data to be loaded
        while self.msg_bus.qsize() > 0:
            sleep(0.1)
        self.midi_keepalive_thread.start()
        # Start Update Thread to listen for config changes
        self.midi_keepalive_thread.join()

    def apc_grid_event(self, event) -> None:
        if self.display_view not in [0, 7]:
            # Skip if not in the correct view
            return
        if (self.display_view == 7 and event.state
                and self.apc.shift and event.x in [4, 5, 6]):
            # NOTE: Master Unlock
            if event.x == 4 and event.y == 7:
                # Reset the unlock
                self.apc_master_lock_entry = []
                self.apc.gridbuttons.set_led(4, 7, "red", "bright")
                self.lcdsender.send(
                    "on_next_or_id",
                    ["WARN: Master", "Locked"],
                    "lock_status"
                )
                return
            if self.apc_master_lock_entry == self.apc_master_lock:
                # Already unlocked
                return
            if (event.x, event.y) == self.apc_master_lock[len(self.apc_master_lock_entry)]:  # noqa: E501
                self.apc_master_lock_entry.append((event.x, event.y))
                if self.apc_master_lock_entry == self.apc_master_lock:
                    self.apc.gridbuttons.set_led(4, 7, "green", "bright")
                    self.lcdsender.send(
                        "on_next_or_id",
                        ["INFO: Master", "Unlocked"],
                        "lock_status"
                    )
                return
        if self.display_view == 7 and event.state:
            if self.apc_master_lock_entry != self.apc_master_lock:
                self.lcdsender.send(
                    "on_next_or_id",
                    ["MASTER FXRETURN", "LOCKED"],
                    "lock_status"
                )
                return
            if event.x in range(4):
                self.sender.mix(
                    event.x,
                    self.midi_grid_to_soundcraft(event.y),
                    "f"
                )
                self.apc_last_used_channel = int(event.x)
                return
            if event.x == 7:
                self.sender.master(self.midi_grid_to_soundcraft(event.y))
                self.apc_last_used_channel = int(event.x)
                return
        if self.display_view == 0 and event.state:
            # NOTE: Set Channel Mix from Grid
            self.sender.mix(
                event.x + self.channels_index,
                self.midi_grid_to_soundcraft(event.y),
                "i"
            )
            self.apc_last_used_channel = int(event.x)

    def apc_side_event(self, event) -> None:
        if event.button_id == 0 and self.display_view != 0:
            self.display_view = 0
            self.apc_last_used_channel = None
            self.apc.display_mix_channels()
        elif event.button_id == 7 and self.display_view != 7:
            self.apc_master_lock_entry = []
            self.display_view = 7
            self.apc_last_used_channel = None
            self.apc.display_master_fxreturn()

    def apc_lower_event(self, event) -> None:
        if not event.state:
            return
        if self.apc.shift and self.display_view == 0:
            if event.button_id == 4 and self.apc_last_used_channel is not None:
                # NOTE: Increase last set Mix channel by 0.01 (1%)
                next_value = float(
                    self.channels[str(self.apc_last_used_channel)]["mix"]
                ) + 0.002
                self.sender.mix(
                    self.apc_last_used_channel,
                    next_value if next_value <= 1 else 1,
                    "i"
                )
                return
            if event.button_id == 5 and self.apc_last_used_channel is not None:
                # NOTE: Decrease last set Mix channel by 0.01 (1%)
                next_value = float(
                    self.channels[str(self.apc_last_used_channel)]["mix"]
                ) - 0.002
                self.sender.mix(
                    self.apc_last_used_channel,
                    event.x + self.channels_index,
                    next_value if next_value >= 0 else 0,
                    "i"
                )
                return
            if (event.button_id == 6
                    and self.check_index(self.channels_index - 1, 0, 4)):
                # NOTE: Move channels one to left (-1)
                self.channels_index -= 1
                self.apc.display_mix_channels()
                return
            if (event.button_id == 7
                    and self.check_index(self.channels_index + 1, 0, 4)):
                # NOTE: Move channels one to the right (+1)
                self.channels_index += 1
                self.apc.display_mix_channels()
                return
        if (self.apc.shift and self.display_view == 7
                and self.apc_last_used_channel is not None):
            if event.button_id == 4:
                if self.apc_last_used_channel == 7:
                    next_value = float(self.master) + 0.002
                    self.sender.master(next_value if next_value <= 1 else 1)
                else:
                    next_value = float(
                        self.fx[str(self.apc_last_used_channel)]["mix"]
                    ) + 0.002
                    self.sender.mix(
                        self.apc_last_used_channel,
                        next_value if next_value <= 1 else 1,
                        "f"
                    )
                return
            if event.button_id == 5:
                if self.apc_last_used_channel == 7:
                    next_value = float(self.master) - 0.002
                    self.sender.master(next_value if next_value >= 0 else 0)
                else:
                    next_value = float(
                        self.fx[str(self.apc_last_used_channel)]["mix"]
                    ) - 0.002
                    self.sender.mix(
                        self.apc_last_used_channel,
                        next_value if next_value >= 0 else 0,
                        "f"
                    )
                return
        if not self.apc.shift and self.display_view == 0:
            channel_id = event.button_id + self.channels_index
            self.sender.mute(
                channel_id,
                0 if self.channels[str(channel_id)]["mute"] == "1" else 1,
                "i"
            )
            return
        if not self.apc.shift and self.display_view == 7:
            if event.button_id in range(4):
                self.sender.mix(
                    event.button_id,
                    0,
                    "f"
                )
                return
            if event.button_id == 7:
                self.sender.master(0)

    def apc_fader_event(self, event) -> None:
        """ Event happening when Fader is moved """
        if self.display_view == 0 and event.fader_id in list(range(5)):
            self.sender.fx_setting(
                0,
                event.fader_id + 1,
                self.midi_to_soundcraft(event.value)
            )
        elif self.display_view == 0 and event.fader_id in list(range(5, 9)):
            self.sender.fx_setting(
                1,
                (event.fader_id + 1) - 5,
                self.midi_to_soundcraft(event.value)
            )
        elif self.display_view == 7:
            # NOTE: just enable mixers if code was correctly entered
            if (event.fader_id in [4, 5, 6, 8]
                    or self.apc_master_lock_entry != self.apc_master_lock):
                # disabled fader
                return
            if event.fader_id == 7:
                self.sender.master(self.midi_to_soundcraft(event.value))
            if event.fader_id in range(4):
                # Set fxreturn mix volume
                self.sender.mix(
                    event.fader_id,
                    self.midi_to_soundcraft(event.value),
                    "f"
                )

    def apc_shift_event(self, state):
        if state:
            self.apc.shift = True
        else:
            self.apc.shift = False

    def midi_mix_knob_event(self, event):
        current_knob = (event.x, event.y)
        for check_set in self.KNOB_MAPPING:
            if current_knob in check_set:
                channel = self.KNOB_MAPPING.index(check_set)
                break
        channel += self.channelfxsend_index * 6
        self.sender.fx(
            channel,
            self.midi_to_soundcraft(event.value),
            "i", self.KNOB_MAPPING[channel].index((event.x, event.y))
        )

    def midi_mix_fader_event(self, event):
        if event.fader_id in list(range(3)):
            self.sender.fx_setting(
                2,
                event.fader_id + 1,
                self.midi_to_soundcraft(event.value)
            )
        elif event.fader_id in list(range(3, 8)):
            self.sender.fx_setting(
                3,
                (event.fader_id + 1) - 3,
                self.midi_to_soundcraft(event.value)
            )
        elif event.fader_id == 8:
            # Set the BPM - Values will be 60 to 60 + range(128)  = 187
            self.sender.tempo(
                60 + event.value
            )

    def midi_mix_mute_event(self, event):
        # NOTE: Currently no event set
        # Possible driver for managing the displays?
        pass

    def midi_mix_recarm_event(self, event):
        # NOTE: Currently no event set
        # Possible driver for managing the displays?
        pass

    def midi_mix_bank_event(self, event):
        # NOTE: Move Effect Channels for the Knobs
        if event.state and event.button_id and self.channelfxsend_index:
            self.channelfxsend_index = 0
        if (event.state and not event.button_id
                and not self.channelfxsend_index):
            self.channelfxsend_index = 1

    def midi_mix_solo_event(self, state):
        if state:
            self.midimix.shift = True
        else:
            self.midimix.shift = False

    def get_fx_colour(self, num) -> str:
        if num == 0:
            return "blue"
        elif num == 1:
            return "orange"
        elif num == 2:
            return "magenta"
        else:
            return "green"

    def get_fx_name(self, num) -> str:
        num = int(num)
        if num == 0:
            return "Reverb"
        elif num == 1:
            return "Delay"
        elif num == 2:
            return "Chorus"
        else:
            return "Room"

    def get_fx_parname(self, fx, par) -> str:
        fx = int(fx)
        if par == "bpm" or par == "mute" or par == "mix":
            return par
        if fx == 0 or fx == 3:
            if par == "par1":
                return "Time"
            elif par == "par2":
                return "HF Damping"
            elif par == "par3":
                return "Bass Gain"
            elif par == "par4":
                return "LPF"
            elif par == "par5":
                return "HPF"
        elif fx == 1:
            if par == "par1":
                return "Length"
            elif par == "par2":
                return "Division"
            elif par == "par3":
                return "Feedback"
            elif par == "par4":
                return "LPF"
        elif fx == 2:
            if par == "par1":
                return "Detune"
            elif par == "par2":
                return "Density"
            elif par == "par3":
                return "LPF"
        else:
            return "UNKOWN"

    def get_mix_vals_as_str(self, val) -> str:
        if float(val) >= self.MIX_STD50.x[0]:
            out = round(float(self.MIX_STD50(val)), 1)
        elif float(val) >= self.MIX_STD37.x[0]:
            out = round(float(self.MIX_STD37(val)), 1)
        elif float(val) >= self.MIX_STD18.x[0]:
            out = round(float(self.MIX_STD18(val)), 1)
        elif float(val) >= self.MIX_STD5.x[0]:
            out = round(float(self.MIX_STD5(val)), 1)
        else:
            out = round(float(self.MIX_STD0(val)), 1)
        return f"{out} dB"

    def get_fx_par_vals(self, fx, par) -> str:
        fx = int(fx)
        fx_val = float(self.fx[str(fx)][par])
        sel = int(fx_val * 10 // 1)
        if sel == 10:
            sel = 9
        if par == "bpm":
            return f"{int(fx_val)}"
        if par == "mute":
            return "On" if self.fx[str(fx)][par] == 1 else "Off"
        if par == "mix":
            return self.get_mix_vals_as_str(fx_val)
        if fx == 0:
            if par == "par1":
                return f"{int(self.MAP_TIME_REV[sel](fx_val))} ms"
            elif par == "par2":
                return f"{int(self.MAP_100(fx_val))}%"
            elif par == "par3":
                return f"{int(self.MAP_100(fx_val))}%"
            elif par == "par4":
                val = int(self.MAP_LPF_REV[sel](fx_val))
                if val >= 10e3:
                    return f"{round(val/1000, 1)} kHz"
                elif val >= 10e2:
                    return f"{round(val/1000, 2)} kHz"
                else:
                    return f"{val} Hz"
            elif par == "par5":
                val = int(self.MAP_HPF_REV[sel](fx_val))
                if val >= 10e2:
                    return f"{round(val/1000, 2)} kHz"
                else:
                    return f"{val} Hz"
        elif fx == 1:
            if par == "par1":
                if fx_val == 0:
                    return "SUB DIV MODE"
                else:
                    return f"{int(self.MAP_TIME_DELAY[sel](fx_val))} ms"
            elif par == "par2":
                if self.fx["1"]["par1"] > 0:
                    return "TIME MODE"
                else:
                    return f"{round(float(self.MAP_200(fx_val)), 1)}%"
            elif par == "par3":
                return f"{int(self.MAP_100(fx_val))}%"
            elif par == "par4":
                val = int(self.MAP_LPF_DELAY[sel](fx_val))
                if val >= 10e3:
                    return f"{round(val / 1000, 1)} kHz"
                elif val >= 10e2:
                    return f"{round(val / 1000, 2)} kHz"
                else:
                    return f"{val} Hz"
        elif fx == 2:
            if par == "par1":
                return f"{int(self.MAP_100pm(fx_val))}c"
            elif par == "par2":
                return f"{int(self.MAP_100(fx_val))}%"
            elif par == "par3":
                val = int(self.MAP_LPF_REV[sel](fx_val))
                if val >= 10000:
                    return f"{round(val/1000, 1)} kHz"
                elif val >= 1000:
                    return f"{round(val/1000, 2)} kHz"
                else:
                    return f"{val} Hz"
        elif fx == 3:
            if par == "par1":
                return f"{int(self.MAP_TIME_ROOM[sel](fx_val))} ms"
            elif par == "par2":
                return f"{int(self.MAP_100(fx_val))}%"
            elif par == "par3":
                return f"{int(self.MAP_100(fx_val))}%"
            elif par == "par4":
                val = int(self.MAP_LPF_REV[sel](fx_val))
                if val >= 10e3:
                    return f"{round(val/1000, 1)} kHz"
                elif val >= 10e2:
                    return f"{round(val/1000, 2)} kHz"
                else:
                    return f"{val} Hz"
            elif par == "par5":
                val = int(self.MAP_HPF_REV[sel](fx_val))
                print(f"{val}")
                if val >= 10e2:
                    return f"{round(val/1000, 2)} kHz"
                else:
                    return f"{val} Hz"

    def check_index(self, index, min, max) -> bool:
        """ Make sure the index vars do not reach out of bounce """
        if index < min or index > max:
            return False
        return True

    def midi_to_soundcraft(self, val) -> float:
        """ Format a value given by midi to use it for soundcraft.
            Midi Values: 0 - 127
            Soundcraft:  0 - 1
        """

        return val / 127

    def soundcraft_to_midi(self, val) -> int:
        """ Format a value given by Soundcraft to use for midi display.
            Midi Display:   0 - 7
            Soundcraft:     0 - 1
        """
        return round(8 * float(val))

    def midi_grid_to_soundcraft(self, val) -> float:
        """ Format a value given by midi grid to use it for soundcraft.
            Use Mute for 0
            Midi Values: 0(+1) - 7(+1)
            Soundcraft:  0 - 1
        """
        return (val + 1) / 8

    def update_config_thread(self) -> None:
        """ Thread
            Read Update Queue and update Config
        """
        options_filter = ["digitech", "deesser", "aux", "gate", "eq", "dyn"]
        input_functions_filter = ["mix", "mute", "solo", "gain"]
        fx_functions = ["mix", "mute", "bpm"]
        init_run = True
        while not self.update_exit.is_set():
            if self.msg_bus.qsize() == 0:
                if init_run:
                    init_run = False
                    self.lcdsender.send(
                        "on_next_or_id",
                        ["Config loaded", " "],
                        "config"
                    )
                sleep(0.1)
                continue
            msg = self.msg_bus.get()
            if msg["kind"] not in ["m", "i", "f"]:
                # Skip messages not containing m(aster), i(nput), f(x) information  # noqa: E501
                continue
            if "option" in msg and msg["option"] in options_filter:
                # Skip messages filtered in the options_filter
                continue
            if ((msg["kind"] == "i" and "channel" in msg) and
                    (("option" in msg and msg["option"] == "fx") or
                     ("function" in msg and
                      msg["function"] in input_functions_filter))):
                if msg["channel"] not in self.channels:
                    self.channels[msg["channel"]] = {
                        "fx": {"0": {}, "1": {}, "2": {}, "3": {}}
                    }
                if "option" in msg and msg["option"] == "fx":
                    channel_fx = self.channels[msg["channel"]]["fx"]
                    fx = channel_fx[msg["option_channel"]]
                    fx[msg["function"]] = msg["value"]
                    # NOTE: Display Channel -> FX send data
                    if not init_run:
                        self.lcdsender.send(
                            "on_next_or_id",
                            [
                                f"CH: {msg['channel']} > "
                                f"{self.get_fx_name(msg['option_channel'])}",
                                f"{self.get_mix_vals_as_str(msg['value'])}"
                            ],
                            f"chfxsnd{msg['channel']}"
                            f"{self.get_fx_name(msg['option_channel'])}"
                        )
                    continue
                if ("function" in msg
                        and msg["function"] in input_functions_filter):
                    self.channels[msg["channel"]][msg["function"]] = msg["value"]  # noqa: E501
                    if not init_run:
                        # NOTE: Display on LCD Matrix the set values
                        self.lcdsender.send(
                            "on_next_or_id",
                            [
                                f"CH: {msg['channel']}",
                                f"{self.get_mix_vals_as_str(msg['value'])}"
                            ],
                            f"chmix{msg['channel']}"
                        )
                        if self.display_view == 0:
                            # NOTE Update Channel Mix/Mute/Gain on APC
                            self.apc.update_mix_channel(int(msg['channel']))
                    continue
            if (msg["kind"] == "m" and "channel" in msg
                    and msg["channel"] == "mix"):
                self.master = msg["value"]
                if not init_run:
                    self.lcdsender.send(
                        "on_next_or_id",
                        [
                            "MASTER",
                            f"{self.get_mix_vals_as_str(msg['value'])}"
                        ],
                        "mastermix"
                    )
                    if self.display_view == 7:
                        # NOTE: Update the master channel on apc grid
                        self.apc.update_master_channel()
                continue
            if (msg["kind"] == "f" and "function" in msg
                    and (msg["function"] in fx_functions
                         or match(r"^par\d$", msg["function"]))):
                if msg["channel"] not in self.fx:
                    self.fx[msg["channel"]] = {}
                self.fx[msg["channel"]][msg["function"]] = msg["value"]
                if not init_run:
                    # Note: Display fx Settings on LCD Matrix
                    if self.display_view == 7 and msg["function"] == "mix":
                        # just display fx_return on the grid
                        # other notifications will be displayed on
                        # the display matrix
                        self.apc.update_fxreturn_channel(int(msg["channel"]))
                    if msg["function"] == "bpm":
                        self.lcdsender.send(
                            "on_next_or_id", ["BPM", f"{msg['value']}"],
                            "fxsettingbpm"
                        )
                    else:
                        self.lcdsender.send(
                            "on_next_or_id",
                            [
                                f"{self.get_fx_name(msg['channel'])} > "
                                f"{self.get_fx_parname(msg['channel'], msg['function'])}",  # noqa: E501
                                f"{self.get_fx_par_vals(msg['channel'], msg['function'])}"  # noqa: E501
                            ],
                            f"fxsetting{msg['channel']}{msg['function']}"
                        )

    def midi_keepalive(self) -> None:
        reconnect = {
            "midimix": False,
            "apc": False
        }
        try:
            self.apc = APC(
                get_midi_string(self.apc_discovery_string),
                True,
                self
            )
            if self.display_view == 0:
                self.apc.display_mix_channels()
            elif self.display_view == 7:
                self.apc.display_master_fxreturn()
            self.lcdsender.send(
                "on_next_or_id",
                ["INFO: APC", "init complete"],
                "apc_state"
            )
        except:  # noqa: E722
            self.lcdsender.send(
                "on_next_or_id",
                ["ERR: APC", "init failed"],
                "apc_state"
            )
            print("Error init APC")
            self.apc = None
        try:
            self.midimix = Midimix(
                get_midi_string(self.midimix_discovery_string),
                True,
                self
            )
            self.lcdsender.send(
                "on_next_or_id",
                ["INFO: Midimix", "Init complete"],
                "midimix_state"
            )
        except:  # noqa: E722
            self.lcdsender.send(
                "on_next_or_id",
                ["ERR: Midimix", "Init failed!"],
                "midimix_state"
            )
            print("Error init MIDI Mix")
            self.midimix = None
        while not self.midi_keepalive_exit.is_set():
            if self.apc and self.apc.ready and not self.apc.is_alive():
                # If the APC is not connected set the flag to reconnect
                reconnect["apc"] = True
            if reconnect["apc"] and self.apc.is_alive():
                # if apc is connected again and in reconnect mode
                # then create the apc and load our config
                self.apc = APC(self.apc.midi_string, True, self)
                if self.display_view == 0:
                    self.apc.display_mix_channels()
                elif self.display_view == 7:
                    self.apc.display_master_fxreturn()
                self.lcdsender.send(
                    "on_next_or_id",
                    ["APC connected", "Ready!"],
                    "apc_state"
                )
                # Disable reconnect mode
                reconnect["apc"] = False
            if (self.midimix and self.midimix.ready
                    and not self.midimix.is_alive()):
                # If MIDIMix is not connected set the reconnect flag
                reconnect["midimix"] = True
            if reconnect["midimix"] and self.midimix.is_alive():
                # Recreate MIDIMix if its connected again and in Reconnect mode
                self.midimix = Midimix(self.midimix.midi_string, True, self)
                self.lcdsender.send(
                    "on_next_or_id",
                    ["Midimix", "connected"],
                    "midimix_state"
                )
                # Disable reconnect mode
                reconnect["midimix"] = False
            sleep(5)
