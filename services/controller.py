from soundcraft_ui16 import MixerListener, MixerSender
# from lcd_i2c_display_matrix.lcd_websocket_sender import MatrixCommandSender
from .midi_controller import APC, Midimix, get_midi_string
from .config import Config, MASTER_LOCK, load_presets, remove_preset
from .formatter import ConfigVars
from queue import Queue
from threading import Thread, Event
from time import sleep
from re import match
from logging import getLogger, INFO
from colorama import Fore


class Controller:
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
            mixer_addr, lcd_addr, args,
            logger: str = "Mixer Controller"
    ) -> None:
        """ Brain of the connection between APC mini mk2 and Soundcraft UI16
            self.apc is the connection to the APC mini mk2.
            self.listener and self.sender are the connection to the Soundcraft
        """
        self.logger = getLogger(logger)
        if self.logger.level < 20:
            self.logger.setLevel(INFO)
        self.args = args
        self.mixer_addr = mixer_addr
        self.lcd_addr = lcd_addr
        self.apc = None
        self.midi_mix = None
        self.apc_discovery_string = r"^APC mini mk2.*?Contr.*?$"
        self.midimix_discovery_string = r"^MIDI Mix.*?$"
        if args.verbose:
            self.logger.info(f"apc discovery: {self.apc_discovery_string}")
            self.logger.info(
                f"midimix discovery: {self.midimix_discovery_string}"
            )
            from mido import get_output_names
            self.logger.info(f"Available Midi Outputs:\n{get_output_names()}")

        # # Soundcraft Control
        self.msg_bus = Queue()
        # Setup sender connection
        if args.verbose:
            self.logger.info("Starting Mixer sender and listener")
        self.sender = MixerSender(mixer_addr, 80, logger_name=self.logger.name)
        self.listener = MixerListener(
            mixer_addr, 80, queue=self.msg_bus,
            logger_name=self.logger.name
        )
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
        self.config = Config(logger_name=self.logger.name)
        self.config_presets = load_presets()
        self.vars = ConfigVars()
        # self.channels = {}
        # self.master = 0
        # self.fx = {}

        # # APC vars
        # Some vars to display the correct
        # values on the APC mini mk2
        self.display_view = 0
        self.channels_index = 0
        self.channelfxsend_index = 0
        self.apc_last_used_channel = None
        self.apc_master_lock = MASTER_LOCK
        self.apc_master_lock_entry = []
        if args.verbose:
            self.logger.info(f"{Fore.GREEN}Mixer Controller setup finished")

    def run(self) -> None:
        """
            Function to start and keep the Controller class alive
            The Controller will start an instance of the apc and midimx
        """
        counter = 0
        while not self.listener.connected:
            self.logger.warning(
                f"Waiting for Mixer connection. Count: {counter}"
            )
            counter += 1
            sleep(.5)
        self.logger.info(
            f"{Fore.GREEN}Mixer is connected! {counter // 2} seconds."
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
                self.logger.warning("Master => locked!")
                return
            if self.apc_master_lock_entry == self.apc_master_lock:
                # Already unlocked
                return
            if (
                (event.x, event.y)
                == self.apc_master_lock[len(self.apc_master_lock_entry)]
            ):
                self.apc_master_lock_entry.append((event.x, event.y))
                if self.apc_master_lock_entry == self.apc_master_lock:
                    self.apc.gridbuttons.set_led(4, 7, "green", "bright")
                    self.logger.warning(f"{Fore.GREEN}Master => unlocked!")
                return
        if self.display_view == 7 and event.state:
            if self.apc_master_lock_entry != self.apc_master_lock:
                self.logger.warning("Master - FX Return -> Locked!")
                return
            if event.x in range(4):
                self.sender.mix(
                    event.x,
                    self.vars.midi_grid_to_soundcraft(event.y),
                    "f"
                )
                self.apc_last_used_channel = int(event.x)
                return
            if event.x == 7:
                self.sender.master(self.vars.midi_grid_to_soundcraft(event.y))
                self.apc_last_used_channel = int(event.x)
                return
        if self.display_view == 0 and event.state:
            # NOTE: Set Channel Mix from Grid
            self.sender.mix(
                event.x + self.channels_index,
                self.vars.midi_grid_to_soundcraft(event.y),
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
                    self.config.get_channel_value(
                        str(self.apc_last_used_channel), "mix"
                    )
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
                    self.config.get_channel_value(
                        str(self.apc_last_used_channel), "mix"
                    )
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
                    next_value = float(self.config.get_master()) + 0.002
                    self.sender.master(next_value if next_value <= 1 else 1)
                else:
                    next_value = float(
                        self.config.get_fx_value(
                            str(self.apc_last_used_channel), "mix"
                        )
                    ) + 0.002
                    self.sender.mix(
                        self.apc_last_used_channel,
                        next_value if next_value <= 1 else 1,
                        "f"
                    )
                return
            if event.button_id == 5:
                if self.apc_last_used_channel == 7:
                    next_value = float(self.config.get_master()) - 0.002
                    self.sender.master(next_value if next_value >= 0 else 0)
                else:
                    next_value = float(
                        self.config.get_fx_value(
                            str(self.apc_last_used_channel), "mix"
                        )
                    ) - 0.002
                    self.sender.mix(
                        self.apc_last_used_channel,
                        next_value if next_value >= 0 else 0,
                        "f"
                    )
                return
        if not self.apc.shift and self.display_view == 0:
            channel_id = event.button_id + self.channels_index
            mute = 1
            if self.config.get_channel_value(str(channel_id), "mute") == "1":
                mute = 0
            self.sender.mute(
                channel_id,
                mute,
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
                self.vars.midi_to_soundcraft(event.value)
            )
        elif self.display_view == 0 and event.fader_id in list(range(5, 9)):
            self.sender.fx_setting(
                1,
                (event.fader_id + 1) - 5,
                self.vars.midi_to_soundcraft(event.value)
            )
        elif self.display_view == 7:
            # NOTE: just enable mixers if code was correctly entered
            if (event.fader_id in [4, 5, 6, 8]
                    or self.apc_master_lock_entry != self.apc_master_lock):
                # disabled fader
                return
            if event.fader_id == 7:
                self.sender.master(self.vars.midi_to_soundcraft(event.value))
            if event.fader_id in range(4):
                # Set fxreturn mix volume
                self.sender.mix(
                    event.fader_id,
                    self.vars.midi_to_soundcraft(event.value),
                    "f"
                )

    def midi_mix_knob_event(self, event) -> None:
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

    def midi_mix_fader_event(self, event) -> None:
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

    def midi_mix_mute_event(self, event) -> None:
        """ Create and load presets """
        if not event.state:
            return None
        if not self.apc.shift and str(event.button_id) in self.config_presets:
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
            not self.apc.shift
            and str(event.button_id) not in self.config_presets
        ):
            # Save config as preset
            self.config.create_preset(str(event.button_id))
            self.config_presets = load_presets()
            self.midimix.mutebuttons.set_led(event.button_id, 1)
        elif self.apc.shift and str(event.button_id) in self.config_presets:
            # Delete a preset
            remove_preset(str(event.button_id))
            del self.config_presets[str(event.button_id)]
            self.midimix.mutebuttons.set_led(event.button_id, 0)
        else:
            # Do nothing no preset is set here
            pass

    def midi_mix_recarm_event(self, event) -> None:
        """ Create and load presets """
        if not event.state:
            return None
        if (
            not self.apc.shift
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
            not self.apc.shift
            and str(event.button_id + 8) not in self.config_presets
        ):
            # Save config as preset
            self.config.create_preset(str(event.button_id + 8))
            self.config_presets = load_presets()
            self.midimix.recarmbuttons.set_led(event.button_id, 1)
        elif (
            self.apc.shift
            and str(event.button_id + 8) in self.config_presets
        ):
            # Delete a preset
            remove_preset(str(event.button_id + 8))
            del self.config_presets[str(event.button_id + 8)]
            self.midimix.recarmbuttons.set_led(event.button_id, 0)
        else:
            # Do nothing no preset is set here
            pass

    def midi_mix_bank_event(self, event) -> None:
        # NOTE: Move Effect Channels for the Knobs
        if event.state and event.button_id and self.channelfxsend_index:
            self.channelfxsend_index = 0
        if (event.state and not event.button_id
                and not self.channelfxsend_index):
            self.channelfxsend_index = 1

    def check_index(self, index, min, max) -> bool:
        """ Make sure the index vars do not reach out of bounce """
        if index < min or index > max:
            return False
        return True

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
                    self.logger.warning("Config has been loaded")
                sleep(0.1)
                continue
            msg = self.msg_bus.get()
            # self.logger.warning(f"{msg}")
            if (
                msg["kind"] not in ["m", "i", "f"]
                or ("option" in msg and msg["option"] in options_filter)
            ):
                # Skip messages not containing m(aster), i(nput), f(x) information  # noqa: E501
                # Skip messages filtered in the options_filter
                continue
            if (
                msg["kind"] == "i"
                and "channel" in msg
                and "option" in msg
                and msg["option"] == "fx"
            ):
                # Update BPM directly because its a global value
                if msg["function"] == "bpm":
                    self.config.update_bpm(msg["value"])
                    continue
                # Update Fx value for a specific Channel
                self.config.update_channel_fx(
                    msg["channel"], msg["option_channel"],
                    msg["function"], msg["value"]
                )
                continue
            if (
                msg["kind"] == "i"
                and "channel" in msg
                and "function" in msg
                and msg["function"] in input_functions_filter
            ):
                # Update Channels function
                self.config.update_channel(
                    msg["channel"], msg["function"], msg["value"]
                )
                if self.display_view == 0 and not init_run:
                    self.apc.update_mix_channel(msg["channel"])
                continue
            if (
                msg["kind"] == "m"
                and "channel" in msg
                and msg["channel"] == "mix"
            ):
                self.config.update_master(msg["value"])
                if self.display_view == 7 and not init_run:
                    # NOTE: Update the master channel on apc grid
                    self.apc.update_master_channel()
                continue
            if (
                msg["kind"] == "f"
                and "function" in msg
                and (
                    msg["function"] in fx_functions
                    or match(r"^par\d$", msg["function"])
                )
            ):
                # Update some value on an fx channel
                self.config.update_fx(
                    msg["channel"], msg["function"], msg["value"]
                )
                if (
                    self.display_view == 7
                    and msg["function"] == "mix"
                    and not init_run
                ):
                    # just display fx_return on the grid
                    # other notifications will be displayed on
                    # the display matrix
                    self.apc.update_fxreturn_channel(int(msg["channel"]))
                    continue

    def midi_keepalive(self) -> None:
        reconnect = {
            "midimix": False,
            "apc": False
        }
        try:
            self.apc = APC(
                get_midi_string(self.apc_discovery_string),
                True, self, self.logger.name
            )
            if self.display_view == 0:
                self.apc.display_mix_channels()
            elif self.display_view == 7:
                self.apc.display_master_fxreturn()
            self.logger.info(f"{Fore.GREEN}APC => Init completed")
        except:  # noqa: E722
            self.logger.critical("APC => Init failed!")
            self.apc = None
        try:
            self.midimix = Midimix(
                get_midi_string(self.midimix_discovery_string),
                True, self, self.logger.name
            )
            self.logger.info(f"{Fore.GREEN}MidiMix => Init completed.")
        except:  # noqa: E722
            self.logger.critical("MidiMix => Init failed!")
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
                self.logger.info(f"{Fore.GREEN}APC connected and ready")
                # Disable reconnect mode
                reconnect["apc"] = False
            if (self.midimix and self.midimix.ready
                    and not self.midimix.is_alive()):
                # If MIDIMix is not connected set the reconnect flag
                reconnect["midimix"] = True
            if reconnect["midimix"] and self.midimix.is_alive():
                # Recreate MIDIMix if its connected again and in Reconnect mode
                self.midimix = Midimix(self.midimix.midi_string, True, self)
                self.logger.info(f"{Fore.GREEN}MidiMix connected and ready")
                # Disable reconnect mode
                reconnect["midimix"] = False
            sleep(5)
