from sqlalchemy.orm import declarative_base
from loguru import logger
import pathlib
import sys
import json
import os

__all__ = ["SqlTableBase", "logger", "config"]

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


class Config:
    def __init__(self):
        self.domain = os.environ.get("CRAWLER_API_DOMAIN", "masothue.com")
        self.rate_limit = int(os.environ.get(
            "CRAWLER_MAX_REQUESTS_PER_SEC", "8")
        )

        __output_path = pathlib.Path.cwd() / "output"
        self.__output_path = os.environ.get(
            "CRAWLER_OUTPUT_PATH", f"{__output_path}"
        )

        db_url = __output_path / "corporate-info.sqlite3.db"
        self.db_url = os.environ.get("CRAWLER_SQL_ENGINE_URL", f"sqlite:///{db_url}")

    @property
    def output_path(self) -> pathlib.Path:
        return pathlib.Path(self.__output_path)


config = Config()
