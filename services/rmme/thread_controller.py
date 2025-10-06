from soundcraft_ui16 import MixerListener, MixerSender
from queue import Queue
from logging import getLogger
from argparse import Namespace
from time import sleep
from datetime import datetime
from .config import MIXER_ADDRESS, MIXER_PORT, Config
from .threads import (
    UpdateConfigThread, ApcControllerThread, MidimixControllerThread,
)
from .gui import BaseFrame
from .wifi import wait_connect
from .gui_controller import GuiController


class ThreadController:
    def __init__(
        self,
        update_queue: Queue,
        config: Config,
        gui: BaseFrame,
        args: Namespace,
        logger_name: str = "ThreadController"
    ) -> None:
        # vars
        self.logger = getLogger(logger_name)
        self.update_queue = update_queue
        self.args = args
        # Threads
        self.sender = MixerSender(
            MIXER_ADDRESS, MIXER_PORT,
            logger_name=self.logger.name
        )
        self.listener = MixerListener(
            MIXER_ADDRESS, MIXER_PORT,
            queue=update_queue, logger_name=self.logger.name
        )
        self.update_thread = UpdateConfigThread(
            update_queue, config, self.logger.name, self
        )
        self.apc_keepalive_thread = ApcControllerThread(
            self.sender, config, args, self.logger.name, self
        )
        self.midimix_keepalive_thread = MidimixControllerThread(
            self.sender, config, args, self.logger.name, self
        )
        self.gui_controller = GuiController(
            gui, config, self.logger.name, self
        )

    def terminate(self) -> None:
        self.sender.terminate()
        self.listener.terminate()
        self.update_thread.terminate()
        self.apc_keepalive_thread.terminate()
        self.midimix_keepalive_thread.terminate()
        # self.gui_controller.terminate()

    def test(self) -> None:
        self.logger.warning("This is a test")
        self.logger.info("APC => Starting")
        self.apc_keepalive_thread.start()

    def start(self) -> None:
        self._check_network_connection()
        setup_listener = True
        self.logger.info("Starting listener...")
        while setup_listener:
            self.listener.start()
            self._check_mixer_connection(self.listener)
            sleep(1)
            if self.update_queue.qsize() == 0:
                # Make sure we do not just throw the thread away.
                # we need to clean stuff up
                self.listener.terminate()
                self.listener = MixerListener(
                    MIXER_ADDRESS, MIXER_PORT,
                    queue=self.update_queue, logger_name=self.logger.name
                )
                sleep(.5)
                self.logger.warning("Listener did not send messages. Restart")
            else:
                setup_listener = False
        self.logger.info("Listener => ready!")
        self.logger.info("Sender => starting")
        self.sender.start()
        self._check_mixer_connection(self.sender)
        self.logger.info("Sender => ready")
        self.logger.info("Update Thread => starting")
        self.update_thread.start()
        self._wait_for_updates()
        self.logger.info("Update Thread => Ready")
        self.logger.info("APC => Starting")
        self.apc_keepalive_thread.start()
        self.logger.info("Midimix => Starting")
        self.midimix_keepalive_thread.start()
        self.logger.info("Gui => Starting")
        # self.gui_controller.start()
        self.logger.info(
            "All Functions are now indepentend! "
            "Happy to help => Back into the control room."
        )

    def _wait_for_updates(self) -> None:
        while self.update_queue.qsize() > 0:
            sleep(.2)
        self.logger.warning("Update Thread => All updates read")

    def _check_mixer_connection(self, connection) -> None:
        if self.args.skip_network_check:
            return None
        start = datetime.now()
        while not connection.connected:
            self.logger.warning(
                "Waiting for Mixer connection ... "
                f"{(datetime.now() - start).seconds}s"
            )
            sleep(.5)
        self.logger.info(
            f"Mixer connected. Took {(datetime.now() - start).seconds} seconds"
        )

    def _check_network_connection(self) -> None:
        """ Check if connected to soundcraft wifi
            TODO: Improve since its blocking the programm
        """
        wait_connect(
            self.args.skip_network_check,
            logger_name=self.logger.name
        )

    def notify_update(self, key: str, data: dict = {}) -> None:
        if key == "bpm":
            self.gui_controller.update_settings({"key": key, "data": data})
        elif key == "channel_fx":
            self.gui_controller.update_settings({"key": key, "data": data})
        elif key == "channel":
            self.gui_controller.update_settings({"key": key, "data": data})
            if self.apc_keepalive_thread.apc:
                self.apc_keepalive_thread.apc.update_settings(
                    {"key": key, "data": data}
                )
        elif key == "master":
            self.gui_controller.update_settings({"key": key})
            if self.apc_keepalive_thread.apc:
                self.apc_keepalive_thread.apc.update_settings({"key": key})
        elif key == "fx":
            if data["function"] == "mix":
                if self.apc_keepalive_thread.apc:
                    self.apc_keepalive_thread.apc.update_settings(
                        {"key": "fxmix", "data": data}
                    )
                self.gui_controller.update_settings(
                    {"key": "fxmix", "data": data}
                )
            elif "par" in data["function"]:
                self.gui_controller.update_settings(
                    {"key": "fxpar", "data": data}
                )
        elif key == "channel_move":
            self.gui_controller.update_settings(
                {"key": key, "data": data}
            )
        elif key == "fx_move":
            self.gui_controller.update_settings(
                {"key": key}
            )
        elif key == "apc_shift":
            self.gui_controller.update_settings(
                {"key": key, "data": data}
            )
            if self.midimix_keepalive_thread.midimix:
                self.midimix_keepalive_thread.midimix.update_settings(
                    {"key": key, "data": data}
                )
        elif key == "midimix_shift":
            self.gui_controller.update_settings(
                {"key": key, "data": data}
            )
            if self.apc_keepalive_thread.apc:
                self.apc_keepalive_thread.apc.update_settings(
                    {"key": key, "data": data}
                )
        elif key == "matrix_view":
            self.gui_controller.update_settings(
                {"key": key, "data": data}
            )
        else:
            return None
