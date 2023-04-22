import requests
from lxml import etree

import sqlalchemy
from sqlalchemy.exc import IntegrityError as SqlIntegrityError
from sqlalchemy import Engine as SqlEngine
from sqlalchemy.orm import declarative_base, Session as SqlSession
from sqlalchemy import Column as SqlColumn, String as SqlString, Integer as SqlInteger

from .common import *


_region_levels = {1: "Tỉnh, thành phố", 2: "Quận, huyện", 3: "Phường, xã"}


class Region(SqlTableBase):
    __tablename__ = "regions"
    id = SqlColumn(SqlString, primary_key=True)
    name = SqlColumn(SqlString)
    level = SqlColumn(SqlInteger)
    level_name = SqlColumn(SqlString)
    url = SqlColumn(SqlString)
    parent_id = SqlColumn(SqlString)
    parent_name = SqlColumn(SqlString)

    @classmethod
    def create_table(Self, engine: sqlalchemy.Engine):
        Self.metadata.create_all(engine)

    def __str__(self) -> str:
        self_repr = f"{self.level_name} {self.name}"
        parent_repr = f"{_region_levels[self.level]} {self.parent_name}"
        if self.parent_id in ["", None]:
            return self_repr
        return f"{parent_repr} - {self_repr}"


class RegionCrawler:
    def __init__(self,  storage_engine: SqlEngine):
        self.storage_engine = storage_engine
        Region.create_table(self.storage_engine)

    def crawl(self):
        self._crawl_first_level()   # Provinces, Cities
        self._crawl_other_level(2)  # Districts
        self._crawl_other_level(3)  # Communes

    def _extract_region_info(self, url: str, level: int):
        # Fetch content from url
        resp = requests.get(url)
        try:
            resp.raise_for_status()
        except Exception as err:
            logger.error(f"Failed to get data from {url} with error {err}")
            return

        # Extract data from response
        document = etree.HTML(resp.text)
        query = '//div[@id = "sidebar"]//ul/li'
        regions = []
        for elem in document.xpath(query):
            try:
                url = elem.xpath('.//a/@href')[0]
                name = elem.xpath('.//a//text()')[0]
                id = url.split("-")[-1]
            except Exception as err:
                logger.error(f"Failed to extract region info from {url}")
                continue

            region = Region(
                id=id,
                name=name,
                level=level,
                level_name=_region_levels[level],
                url=url,
                parent_id=None,
                parent_name=None
            )
            regions.append(region)

        # Store data into storage
        with SqlSession(self.storage_engine) as session:
            for region in regions:
                if session.get(Region, ident=region.id) == None:
                    session.add(region)
            session.commit()

        logger.success(
            f"Extract and store {len(regions)} region records from {url}"
        )

    def _crawl_first_level(self):
        url = f"https://{BASE_URL}"
        self._extract_region_info(url, level=1)
        logger.success(
            f"Got all regions at level 1 - {_region_levels[1]}")

    def _crawl_other_level(self, level: int):
        with SqlSession(self.storage_engine) as session:
            regions_iter = session.query(Region).where(Region.level == level-1)
            regions = list(regions_iter)

        for region in regions:
            url = f"https://{BASE_URL}{region.url}"
            self._extract_region_info(url, level=level)
            logger.success(f"Got all sub-regions of {region}")
