# app_logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.INFO, maxBytes=10000, backupCount=3):
    """
    Initialize and configure a logger with rotation handling.

    This function sets up a logger with a specified name and log file. It configures the logger to rotate the log file
    when it reaches a certain size, keeping a specified number of backup files. This is useful for keeping log files
    manageable and avoiding excessively large log files.

    Parameters:
    - name (str): The name of the logger. This is typically the module name or the functionality area the logs pertain to.
    - log_file (str): Path to the log file where logs will be written.
    - level (logging.LEVEL, optional): The logging level. Determines the severity of messages that will be logged.
      Defaults to logging.INFO.
    - maxBytes (int, optional): The maximum size in bytes of the log file before it is rotated. Defaults to 10,000 bytes.
    - backupCount (int, optional): The number of backup log files to keep. Defaults to 3.

    Returns:
    logging.Logger: A configured Logger instance that writes to the specified file and rotates logs as configured.

    Example usage:
    logger = setup_logger('my_app', '/path/to/your/logfile/app.log')
    logger.info('This is an informational message.')
    """

    # Create a handler that writes log messages to a file, rotating the log file at a specified size.
    handler = RotatingFileHandler(log_file, maxBytes=maxBytes, backupCount=backupCount)

    # Define the format of the log messages.
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Apply the formatter to the handler.
    handler.setFormatter(formatter)

    # Get or create a logger with the specified name.
    logger = logging.getLogger(name)

    # Set the logging level for the logger.
    logger.setLevel(level)

    # Add the handler to the logger, completing its configuration.
    logger.addHandler(handler)

    # Return the configured logger.
    return logger
