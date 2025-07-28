#!/home/dhoessl/venvs/midi2soundcraft/bin/python
# external import
from PySide6.QtWidgets import QApplication, QMainWindow
from queue import Queue
from argparse import Namespace
# private import
from services.gui.config import WINDOW_CONFIG  # , MIXER_ADDRESS
from services.gui.base import BaseFrame
from services.args import get_args
from services.logger import get_logger
from services.thread_controller import ThreadController
from services.config import Config


class GUIApplication(QApplication):
    def __init__(self, args: Namespace) -> None:
        super().__init__([])
        self.widget_main = BaseFrame()

        logger_name = "Midi2Soundcraft"
        self.logger = get_logger(
            logger_name, args.logfile, args.colored_log
        )

        self.update_queue = Queue()
        self.apc_queue = Queue()
        self.midimix_queue = Queue()
        self.gui_queue = Queue()
        self.config = Config(self.logger.name)

        thread_controller = ThreadController(
            self.update_queue, self.apc_queue,
            self.midimix_queue, self.gui_queue,
            self.config, self.widget_main, args,
            self.logger.name
        )
        if args.test:
            thread_controller.test()
        else:
            thread_controller.start()

        window = self._create_main_window()
        window.show()
        self.exec()
        thread_controller.terminate()

    def _create_main_window(self) -> QMainWindow:
        window = QMainWindow()
        window.setStyleSheet("background-color: #A7AFB6;")
        window.setWindowTitle("Midi and Soundcraft")
        geo = WINDOW_CONFIG["geometry"]
        window.setGeometry(
            geo["x"], geo["y"],
            geo["width"], geo["height"]
        )
        window.setCentralWidget(self.widget_main)
        return window


if __name__ == "__main__":
    args = get_args()
    GUIApplication(args)
