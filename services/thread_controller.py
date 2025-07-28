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
        apc_queue: Queue,
        midimix_queue: Queue,
        gui_queue: Queue,
        config: Config,
        gui: BaseFrame,
        args: Namespace,
        logger_name: str = "ThreadController"
    ) -> None:
        # vars
        self.logger = getLogger(logger_name)
        self.apc = None
        self.midimix = None
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
            update_queue, apc_queue, midimix_queue, gui_queue,
            config
        )
        self.apc_keepalive_thread = ApcControllerThread(
            apc_queue, gui_queue, midimix_queue,
            self.sender, config, self.logger.name
        )
        self.midimix_keepalive_thread = MidimixControllerThread(
            midimix_queue, gui_queue, apc_queue,
            self.sender, config, self.logger.name
        )
        self.gui_controller = GuiController(
            gui, config, gui_queue, self.logger.name
        )

    def terminate(self) -> None:
        self.sender.terminate()
        self.listener.terminate()
        self.update_thread.terminate()
        self.apc_keepalive_thread.terminate()
        self.midimix_keepalive_thread.terminate()
        self.gui_controller.terminate()

    def start(self) -> None:
        self._check_network_connection()
        setup_listener = True
        self.logger.info("Starting listener...")
        while setup_listener:
            self.listener.start()
            self._check_mixer_connection(self.listener)
            if self.update_queue.qsize() < 1:
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
        self.gui_controller.start()
        self.logger.debug(
            "All Functions are now indepentend! "
            "Happy to help => Back into the control room."
        )

    def _wait_for_updates(self) -> None:
        while self.update_queue.qsize() > 0:
            sleep(.1)
        self.logger.info("Update Thread => All updates read")

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
        self.logger.debug(
            f"Mixer connected. Took {(datetime.now() - start).seconds} seconds"
        )

    def _check_network_connection(self) -> None:
        """ Check if connected to soundcraft wifi i
            TODO: Improve since its blocking the programm
        """
        wait_connect(
            self.args.skip_network_check,
            logger_name=self.logger.name
        )
