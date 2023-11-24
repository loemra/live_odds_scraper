import logging


def setup_logging(name, propagate=False, mode="w"):
    logger = logging.getLogger(name)
    handler = logging.FileHandler(
        filename=f"logs/{name}.log",
        mode=mode,
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s : %(name)s - %(levelname)s - %(lineno)d @ %(message)s"
        )
    )
    logger.addHandler(handler)
    logger.propagate = propagate

    return logger


def setup_root_logging():
    logger = logging.getLogger("packages")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s @ %(name)s - %(levelname)s - %(lineno)d : %(message)s"
        )
    )
    logger.addHandler(handler)

    return logger


def setup_seleniumwire_logging():
    sw_handler = logging.FileHandler("logs/seleniumwire.log")
    sw_handler.setFormatter(
        logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    )
    sw_logger = logging.getLogger("seleniumwire")
    sw_logger.setLevel(logging.INFO)
    sw_logger.addHandler(sw_handler)
