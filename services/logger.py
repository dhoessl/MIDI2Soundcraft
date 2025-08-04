from colorama import Fore, Style
from logging import (
    StreamHandler, FileHandler, Formatter,
    getLogger, Logger,
    DEBUG, INFO, WARNING, ERROR, CRITICAL
)
from sys import stdout
from os import path
from pathlib import Path

LOGGING_FILE = "/var/log/midi2soundcraft.log"


class ColoredFormatter(Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    message_format = "%(asctime)s - %(filename)s => %(funcName)s\n"
    message_format += "\t%(levelname)s: %(message)s"

    FORMATS = {
        DEBUG: Fore.GREEN + message_format + Style.RESET_ALL,
        INFO: Fore.WHITE + message_format + Style.RESET_ALL,
        WARNING: Fore.YELLOW + message_format + Style.RESET_ALL,
        ERROR: Fore.RED + message_format + Style.RESET_ALL,
        CRITICAL: Fore.RED + message_format + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = Formatter(log_fmt)
        return formatter.format(record)


def get_logger(name: str, logfile: str, colored: bool = False) -> Logger:
    if logfile and not path.exists(logfile):
        try:
            Path(logfile).touch()
        except PermissionError:
            logfile = None
    logger = getLogger(name)
    # Create logger to the console
    console_handler = StreamHandler(stream=stdout)
    if not colored:
        console_formatter = Formatter(
            "%(asctime)s - %(filename)s => %(funcName)s\n"
            "\t%(levelname)s: %(message)s"
        )
    else:
        console_formatter = ColoredFormatter()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    # Create logger to a file
    if logfile:
        file_handler = FileHandler(logfile)
        file_formatter = Formatter(
            "%(asctime)s - %(filename)s => %(funcName)s "
            "%(levelname)s %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    # add handlers
    logger.setLevel(DEBUG)
    logger.debug("Logger is setup and ready")
    return logger
