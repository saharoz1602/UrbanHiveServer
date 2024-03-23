# app_logger.py
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(name, log_file, level=logging.INFO, maxBytes=10000, backupCount=3):
    """Function setup as many loggers as you want"""

    handler = RotatingFileHandler(log_file, maxBytes=maxBytes, backupCount=backupCount)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
