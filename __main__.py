import pathlib
import sqlalchemy

from crawler.region import RegionCrawler


def main():
    output_path = pathlib.Path.cwd() / "output"
    output_path.mkdir(exist_ok=True)
    db_path = output_path / "corporate-info.sqlite3.db"
    storage_engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")

    crawler = RegionCrawler(storage_engine)
    crawler.crawl()


if __name__ == "__main__":
    main()
