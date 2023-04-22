import pathlib
import sqlalchemy

from crawler.region import RegionCrawler

if __name__ == "__main__":
    db_path = pathlib.Path(".") / "foobar.db"
    storage_engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")
    crawler = RegionCrawler(storage_engine)
    crawler.crawl()
