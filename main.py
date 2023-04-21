from crawler.storage import Storage
from crawler.locations import LocationCrawler

if __name__ == "__main__":
    storage = Storage("foobar.db")
    crawler = LocationCrawler(storage)
    crawler._crawl_first_level()
    crawler._crawl_other_level(level=2)
    crawler._crawl_other_level(level=3)
