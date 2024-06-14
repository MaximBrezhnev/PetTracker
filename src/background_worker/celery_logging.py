import logging


logger = logging.getLogger('worker_logger')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('background_worker.log')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def log_event_not_found(identifier):
    message = f"Событие с указанным идентификатором не найдено: {identifier}"
    logger.info(message)


def log_error(error_message):
    logger.error(error_message)