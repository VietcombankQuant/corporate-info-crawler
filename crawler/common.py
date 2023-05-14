from sqlalchemy.orm import declarative_base
from loguru import logger
import pathlib
import sys
import random
import os

from .ratelimit import RateLimiter
from .api_gateway import ApiGateway

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
        self.source_uri = "https://masothue.com"
        self.__api_gateways = {}

        rate_limit = os.environ.get("CRAWLER_MAX_REQUESTS_PER_SEC", "8")
        rate_limit = int(rate_limit)
        self.rate_limiter = RateLimiter(rate_limit)

        max_retries = os.environ.get("CRAWLER_MAX_RETRIES", "3")
        self.max_retries = int(max_retries)

        __output_path = pathlib.Path.cwd() / "output"
        self.__output_path = os.environ.get(
            "CRAWLER_OUTPUT_PATH", f"{__output_path}"
        )

        db_url = __output_path / "corporate-info.sqlite3.db"
        self.db_url = os.environ.get(
            "CRAWLER_SQL_ENGINE_URL", f"sqlite:///{db_url}"
        )

    def remove_gateway(self, endpoint):
        if endpoint in self.__api_gateways:
            del self.__api_gateways[endpoint]

    def new_gateway(self) -> ApiGateway:
        gateway = ApiGateway(self.source_uri)
        self.__api_gateways[gateway.endpoint] = gateway
        return gateway

    @property
    def output_path(self) -> pathlib.Path:
        return pathlib.Path(self.__output_path)

    @property
    def domain(self) -> str:
        if len(self.__api_gateways) == 0:
            gateway = self.new_gateway()
            return gateway.endpoint

        gateway = random.choice(list(self.__api_gateways.values()))
        return gateway.endpoint


config = Config()
