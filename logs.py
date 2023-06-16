import logging

def setup_logging(logger_level=logging.INFO):
    logging.basicConfig(filename='std.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logger_level)
    return logger

logger = setup_logging()