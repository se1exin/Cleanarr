import os
import logging
from sys import stdout


def get_logger(name):
    # Define logger
    level = logging.DEBUG if os.environ.get("DEBUG", "0") == "1" else logging.ERROR
    logger = logging.getLogger(name)

    logger.setLevel(level)
    log_formatter = logging.Formatter("%(name)-12s %(asctime)s %(levelname)-8s %(filename)s:%(funcName)s %(message)s")
    console_handler = logging.StreamHandler(stdout)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    return logger
