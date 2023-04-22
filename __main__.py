import pathlib
import sqlalchemy

from crawler.region import RegionCrawler

if __name__ == "__main__":
    output_path = pathlib.Path("output")
    if not output_path.exists():
        output_path.mkdir()
    db_path = output_path / "corporate-info.sqlite3.db"
    storage_engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")

    crawler = RegionCrawler(storage_engine)
    crawler.crawl()
