from soundcraft_ui16 import MixerListener, MixerSender
from queue import Queue
from argparse import Namespace
from time import sleep
from datetime import datetime
from loguru import logger

from services.core import (
    MIXER_ADDRESS, MIXER_PORT, Config, wait_connect
)
from services.threads import (
    UpdateConfigThread, ApcControllerThread, MidimixControllerThread,
)
from services.gui import BaseFrame
from services.gui_controller import GuiController
from services.flask.webapp import WebApp


class ThreadController:
    def __init__(
        self, update_queue: Queue, config: Config, args: Namespace,
        gui: BaseFrame | WebApp
    ) -> None:
        # vars
        self.update_queue = update_queue
        self.args = args
        # Threads
        self.sender = MixerSender(
            MIXER_ADDRESS, MIXER_PORT
        )
        self.listener = MixerListener(
            MIXER_ADDRESS, MIXER_PORT,
            queue=update_queue
        )
        self.update_thread = UpdateConfigThread(
            update_queue, config, self
        )
        self.apc_keepalive_thread = ApcControllerThread(
            self.sender, config, args, self
        )
        self.midimix_keepalive_thread = MidimixControllerThread(
            self.sender, config, args, self
        )
        if type(gui) is BaseFrame:
            self.gui_controller = GuiController(
                gui, config, self
            )
        elif type(gui) is WebApp:
            self.gui_controller = gui
            self.gui_controller.thread_controller = self
        else:
            raise RuntimeError(f"Gui of type {type(gui)} not implemented")

    def terminate(self) -> None:
        self.sender.terminate()
        self.listener.terminate()
        self.update_thread.terminate()
        self.apc_keepalive_thread.terminate()
        self.midimix_keepalive_thread.terminate()
        # TODO: Add a terminate button in gui and shut it down too
        # self.gui_controller.terminate()

    def test(self) -> None:
        print("Nothing to test")

    def start(self) -> None:
        self._check_network_connection()
        setup_listener = True
        logger.info("Starting listener...")
        while setup_listener:
            self.listener.start()
            self._check_mixer_connection(self.listener)
            sleep(1)
            if self.update_queue.qsize() == 0:
                # Make sure we do not just throw the thread away.
                # we need to clean stuff up
                self.listener.terminate()
                self.listener = MixerListener(
                    MIXER_ADDRESS, MIXER_PORT, queue=self.update_queue
                )
                sleep(.5)
                logger.warning("Listener did not send messages. Restart")
            else:
                setup_listener = False
        logger.info("Listener => ready!")
        logger.info("Sender => starting")
        self.sender.start()
        self._check_mixer_connection(self.sender)
        logger.info("Sender => ready")
        logger.info("Update Thread => starting")
        self.update_thread.start()
        self._wait_for_updates()
        logger.info("Update Thread => Ready")
        logger.info("APC => Starting")
        self.apc_keepalive_thread.start()
        logger.info("Midimix => Starting")
        self.midimix_keepalive_thread.start()
        if type(self.gui_controller) is GuiController:
            logger.info("Update GUI => Starting")
            self.gui_controller.update_settings({"key": "init"})
        logger.info(
            "All Functions are now indepentend! "
            "Happy to help => Back to the control room."
        )

    def _wait_for_updates(self) -> None:
        while self.update_queue.qsize() > 0:
            sleep(.2)
        logger.info("Update Thread => All updates read")

    def _check_mixer_connection(self, connection) -> None:
        if self.args.skip_network_check:
            return None
        start = datetime.now()
        while not connection.connected:
            logger.warning(
                "Waiting for Mixer connection ... "
                f"{(datetime.now() - start).seconds}s"
            )
            sleep(.5)
        logger.info(
            f"Mixer connected. Took {(datetime.now() - start).seconds} seconds"
        )

    def _check_network_connection(self) -> None:
        """ Check if connected to soundcraft wifi
            TODO: Improve since its blocking the programm
        """
        wait_connect(self.args.skip_network_check)

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
