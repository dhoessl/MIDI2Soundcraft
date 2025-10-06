from sys import stderr
from loguru import logger


def define_logger(debug: bool) -> None:
    log_level = "INFO"
    log_format = (
        "<level>{message}</level>"
    )
    if debug:
        log_level = "DEBUG"
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}:{function}</cyan>:<cyan>{line}</cyan> "
            "- <level>{message}</level>"
        )
    logger.remove()
    logger.add(stderr, format=log_format, level=log_level, colorize=True)
    logger.info("MIDI2Soundcraft logger started")
