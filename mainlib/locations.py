import sqlite3
import requests
from lxml import etree
import time

from .storage import Storage
from .constants import *
from .common_types import Location


class LocationCrawler:
    def __init__(self,  storage: Storage):
        self.storage = storage

    def _crawl_first_level(self):
        url = f"https://{BASE_URL}"
        resp = requests.get(url)
        resp.raise_for_status()

        document = etree.HTML(resp.text)
        query = '//div[@id = "sidebar"]//ul/li'
        for elem in document.xpath(query):
            url = elem.xpath('.//a/@href')[0]
            name = elem.xpath('.//a//text()')[0]
            id = url.split("-")[-1]
            location = Location(
                id=id,
                name=name,
                level=1,
                level_name="Tỉnh, thành phố",
                url=f"https://{BASE_URL}{url}",
                parent_id=None,
                parent=None
            )

            try:
                self.storage.new_location(location)
            except sqlite3.IntegrityError:
                pass
        print("DONE: got all administrative level at level 1")

    def _crawl_other_level(self, level: int):
        locations = self.storage.locations(level-1)
        for location in locations:
            resp = requests.get(location.url)
            resp.raise_for_status()

            document = etree.HTML(resp.text)
            query = '//div[@id = "sidebar"]//ul/li'

            for elem in document.xpath(query):
                try:
                    url = elem.xpath('.//a/@href')[0]
                    name = elem.xpath('.//a//text()')[0]
                    id = url.split("-")[-1]
                except Exception:
                    print(f"ERROR: {location.__dict__}")
                    continue 

                location = Location(
                    id=id,
                    name=name,
                    level=level,
                    level_name=["Quận, huyện", "Phường, xã"][level-2],
                    url=f"https://{BASE_URL}{url}",
                    parent_id=location.id,
                    parent=location.name
                )

                try:
                    self.storage.new_location(location)
                except sqlite3.IntegrityError:
                    pass
            print(f"DONE: got all sub-units for {location.name}")
