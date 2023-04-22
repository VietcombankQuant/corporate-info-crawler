from sqlalchemy.orm import declarative_base
from loguru import logger
import pathlib
import sys
import json

__all__ = ["BASE_URL", "SqlTableBase", "logger", "config"]

BASE_URL = "wkajyoa4n5.execute-api.ap-southeast-1.amazonaws.com"
SqlTableBase = declarative_base()


def configure_logger():
    logger_format = (
        "<green>{time}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    log_path = pathlib.Path.cwd() / "output" / "logs"
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "log_{time}.txt"

    logger.remove()
    logger.add(sys.stdout, format=logger_format)
    logger.add(log_file, format=logger_format, rotation="64 MB", enqueue=True)

    return logger


logger = configure_logger()


def __config():
    CONFIG_FILE = pathlib.Path.cwd() / "config.json"
    if not CONFIG_FILE.exists():
        logger.critical(
            'File config.json not exists. Run "python setup.py" and try again.'
        )
        sys.exit(1)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


config = __config()
