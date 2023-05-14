import asyncio
import sqlalchemy
import signal
import sys

from crawler.region import RegionCrawler
from crawler.corporate import CorporateCrawler
from crawler.common import config


def sigint_handler(*args):
    config.remove_all_gateways()
    sys.exit(1)


signal.signal(signal.SIGINT, sigint_handler)


async def main():
    for _ in range(8):
        config.new_gateway()

    config.output_path.mkdir(exist_ok=True)
    storage_engine = sqlalchemy.create_engine(config.db_url)

    crawler = RegionCrawler(storage_engine)
    await crawler.crawl()

    crawler = CorporateCrawler(storage_engine)
    await crawler.crawl()


if __name__ == "__main__":
    asyncio.run(main())
