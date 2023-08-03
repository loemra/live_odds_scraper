import logging.config
import os
from copy import deepcopy


def get_mods():
    mods = []
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                mods.append(os.path.join(root, file)[2:-3].replace("/", "."))
    return mods


def logger_converter(key_val):
    (key, logger) = key_val
    logger["handlers"].append(key)
    return key, logger


def handler_converter(key_val):
    (key, handler) = key_val
    file_name = key.replace(".", "-")
    handler["filename"] = handler["filename"].format(file_name)
    return key, handler


def setup():
    mods = get_mods()

    os.makedirs("logs", exist_ok=True)

    logger = {"level": "DEBUG", "propagate": False, "handlers": []}
    root_logger = {"level": "INFO", "handlers": ["stream"]}
    logger_overrides = {}

    file_handler = {
        "class": "logging.FileHandler",
        "formatter": "regular",
        "level": "DEBUG",
        "filename": "logs/{}.log",
        "mode": "w",
        "delay": True,
    }
    stream_handler = {
        "class": "logging.StreamHandler",
        "formatter": "regular",
        "level": "DEBUG",
    }
    handler_overrides = {"stream": stream_handler}

    config = {
        "version": 1,
        "formatters": {
            "regular": {
                "format": "%(asctime)s:%(levelname)s:%(lineno)d] %(message)s"
            },
        },
        "handlers": (
            dict(
                map(
                    handler_converter,
                    ((mod, file_handler.copy()) for mod in mods),
                )
            )
            | handler_overrides
        ),
        "loggers": (
            dict(
                map(logger_converter, ((mod, deepcopy(logger)) for mod in mods))
            )
            | logger_overrides
        ),
        "root": root_logger,
    }

    logging.config.dictConfig(config)
    logging.info("Logger setup complete.")
