import logging
import colorlog

from almanac import config

def get_formatter():
    return colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def get_logger():
    handler = colorlog.StreamHandler()
    logger = logging.getLogger()
    logger.setLevel(int(config.logging_level))
    logger.addHandler(handler)
    handler.setFormatter(get_formatter())
    return logger

logger = get_logger()
