import logging


class CeleryLogger:
    def __init__(
            self,
            logger_name: str,
            level: str,
            log_file: str
    ):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def log_not_found_message(self, message: str) -> None:
        self.logger.info(message)

    def log_error(self, error_message: str) -> None:
        self.logger.error(error_message)
