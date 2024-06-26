import logging


class CeleryLogger:
    """Class representing logger for the celery tasks"""

    def __init__(self, logger_name: str, level: str, log_file: str):
        """Initializes celery logger by binding a logger, the necessary logging
        level, a handler and message format to CeleryLogger"""

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def log_not_found_message(self, message: str) -> None:
        """Writes a message to a file when an event is not found"""

        self.logger.info(message)

    def log_error(self, error_message: Exception) -> None:
        """Writes an error message to a file when
        an exception occurs in celery task"""

        self.logger.error(error_message)
