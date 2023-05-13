import asyncio
import pathlib
import sqlalchemy

from crawler.region import RegionCrawler
from crawler.corporate import CorporateCrawler
from crawler.common import config


async def main():
    config.output_path.mkdir(exist_ok=True)
    storage_engine = sqlalchemy.create_engine(config.db_url)

    crawler = RegionCrawler(storage_engine)
    await crawler.crawl()

    crawler = CorporateCrawler(storage_engine)
    await crawler.crawl()


if __name__ == "__main__":
    asyncio.run(main())
