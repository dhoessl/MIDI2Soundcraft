#!/home/dhoessl/venvs/midi2soundcraft/bin/python
from services.controller import Controller
from subprocess import Popen, PIPE
from time import sleep
from logging import (
    StreamHandler, FileHandler, Formatter,
    getLogger, Logger, INFO
)
from sys import stdout
from os import path
from pathlib import Path
from argparse import ArgumentParser, Namespace
from colorama import Fore, Style

LOGGING_FILE = "/var/log/midi2soundcraft.log"


def get_logger(name, logfile) -> Logger:
    if logfile and not path.exists(logfile):
        try:
            Path(logfile).touch()
        except PermissionError:
            logfile = None
    logger = getLogger(name)
    # Create logger to the console
    console_handler = StreamHandler(stream=stdout)
    console_formatter = Formatter(
        "%(asctime)s - %(filename)s => %(funcName)s\n"
        "\t%(levelname)s: %(message)s"
    )
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
    logger.setLevel(INFO)
    logger.info(f"{Fore.GREEN}Logger is setup and ready{Style.RESET_ALL}")
    return logger


def get_args() -> Namespace:
    parser = ArgumentParser(description="")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="enable verbose output"
    )
    parser.add_argument(
        "--skip-network-check",
        action="store_true",
        help="set to debug without proper connection"
    )
    parser.add_argument(
        "--logfile",
        default=None,
        type=str,
        help="log to this file"
    )

    return parser.parse_args()


def wait_connect(skip_check: bool = False) -> None:
    check_network = Popen(
        ["nmcli", "-f", "GENERAL.STATE", "con", "show", "soundcraft"],
        stdout=PIPE,
        stderr=PIPE
    )
    outputstd = b''
    while 'activated' not in outputstd.decode():
        # Waiting till nmcli connection to soundcraft is up
        outputstd, outputstderr = check_network.communicate()
        sleep(.5)
        logger.info("Waiting for soundcraft Wifi...")
        if skip_check:
            outputstd = b"activated"
    logger.info(
        f"{Fore.GREEN}Connection to Soundcraft Wifi exists{Style.RESET_ALL}"
    )
    return None


if __name__ == "__main__":
    args = get_args()
    logger_name = "MIDI2Soundcraft"
    logger = get_logger(logger_name, args.logfile)
    wait_connect(args.skip_network_check)
    controller = Controller("10.10.1.1", "10.10.1.10", logger_name, args)
    controller.run()
