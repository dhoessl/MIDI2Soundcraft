from queue import Queue

from services.webapp import WebApp
from services.args import get_args
from services.logger import get_logger
from services.thread_controller_v2 import ThreadController
from services.config import Config


if __name__ == "__main__":
    logger_name = "Midi2Soundcraft"
    args = get_args()
    logger = get_logger(
        logger_name, args.logfile, args.colored_log
    )
    update_queue = Queue()
    config = Config(logger.name)
    webapp = WebApp(logger, args, config)
    # thread_controller = ThreadController(
    #     update_queue, config, args, webapp, logger_name
    # )
    # thread_controller.start()
    webapp.socketio.run(webapp.app, debug=True)
