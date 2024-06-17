import logging
import os.path


logger = logging.getLogger('worker_logger')
logger.setLevel(logging.DEBUG)

log_file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "worker.log"
)
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def log_not_found_message(message: str) -> None:
    logger.info(message)


def log_error(error_message: str) -> None:
    logger.error(error_message)
