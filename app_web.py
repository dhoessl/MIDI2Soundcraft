from queue import Queue

from services.core import get_args, Config, define_logger
from services.thread_controller_v2 import ThreadController


if __name__ == "__main__":
    args = get_args()
    define_logger(args.debug)
    update_queue = Queue()
    config = Config()
    if args.web:
        from uuid import uuid4
        from services.flask.webapp import WebApp
        app = WebApp(args, config, uuid4())
        thread_controller = ThreadController(
            update_queue, config, args, app
        )
        thread_controller.start()
        app.socketio.run(app.app, debug=args.debug)
    elif args.qt:
        from PySide6.QtWidgets import QApplication, QMainWindow
        from services.gui import BaseFrame, WINDOW_CONFIG
        app = QApplication([])
        widget_main = BaseFrame()
        thread_controller = ThreadController(
            update_queue, config, args, widget_main
        )
        thread_controller.start()
        window = QMainWindow()
        window.setStyleSheet("background-color: #A7AFB6;")
        window.setWindowTitle("Midi and Soundcraft")
        geo = WINDOW_CONFIG["geometry"]
        window.setGeometry(
            geo["x"], geo["y"], geo["width"], geo["height"]
        )
        window.setCentralWidget(widget_main)
        window.show()
        app.exec()
    thread_controller.terminate()
