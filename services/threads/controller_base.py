from soundcraft_ui16 import MixerSender
from mido import get_output_names
from time import sleep
from re import match
from logging import getLogger
from threading import Thread, Event
from argparse import Namespace
from services.config import (
    Config, MIDI_CONTROLLER
)
from services.threads import APC, Midimix


class MidiControllerThread:
    def __init__(
        self,
        sender: MixerSender,
        config: Config,
        args: Namespace,
        parent: None,
        logger_name: str = "MidiControllerThread",
    ) -> None:
        self.sender = sender
        self.config = config
        self.args = args
        self.parent = parent
        self.logger = getLogger(logger_name)
        self.controller = {}
        self.keepalive_thread = Thread(
            target=self._thread,
            args=()
        )
        self.exit_flag = Event()

    def _thread(self) -> None:
        self._create_controller()
        while not self.exit_flag.is_set():
            for controller in self.controller:
                if not self.controller[controller]["controller"]:
                    midi_identifier = self._get_midi_string(
                        self.controller[controller]["discovery"]
                    )
                    if midi_identifier:
                        self.controller[controller]["identifier"] = \
                            midi_identifier
                        self._setup_controller(controller)
                    else:
                        self.logger.critical(
                            f"No Port for {controller} found --- Skipping!"
                        )
                elif not self._is_controller_alive(
                    self.controller[controller]["identifier"]
                ):
                    self.controller[controller]["controller"].loop.stop()
                    self._setup_controller(controller)
                sleep(.5)

    def _is_controller_alive(self, identifier) -> bool:
        if identifier in get_output_names():
            return True
        return False

    def _get_midi_string(self, search) -> str:
        for port in get_output_names():
            result = match(search, port)
            if result:
                return result.group()
        return None

    def _setup_controller(self, name) -> None:
        self.logger.info(f"Setting up {name}!")
        if name == "APC":
            self.controller[name]["controller"] = APC(
                self.controller[name]["identifier"], self.sender, self.config,
                self.args, self.parent, self.logger.name
            )
        elif name == "MidiMix":
            self.controller[name]["controller"] = Midimix(
                self.controller[name]["identifier"], self.sender, self.config,
                self.args, self.parent, self.logger.name
            )
        self.controller[name]["controller"].update_settings({"key": "init"})

    def _create_controller(self) -> None:
        for controller in MIDI_CONTROLLER:
            name = MIDI_CONTROLLER[controller]["name"]
            discovery = MIDI_CONTROLLER[controller]["discovery"]
            self.controller[name] = {
                "identifier": None,
                "controller": None,
                "discovery": discovery
            }

    def start(self) -> None:
        self.keepalive_thread.start()

    def join(self) -> None:
        if self.keepalive_thread.is_alive():
            self.keepalive_thread.join()

    def terminate(self) -> None:
        self.logger.warning("Controllers will be stopped!")
        for controller in self.controller:
            self.controller[controller]["controller"].reset()
            self.controller[controller]["controller"].loop.stop()
        self.exit_flag.set()
        self.join()

    def update_settings(self, msg) -> None:
        for controller in self.controller:
            if (
                "controller" in msg
                and msg["controller"].lower() == controller.lower()
                and self._is_controller_alive(
                    self.controller[controller]["identifier"]
                )

            ):
                self.controller[controller]["controller"].update_settings(msg)
