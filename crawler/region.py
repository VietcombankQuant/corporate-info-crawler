import requests
from lxml import etree

import sqlalchemy
from sqlalchemy.exc import IntegrityError as SqlIntegrityError
from sqlalchemy import Engine as SqlEngine
from sqlalchemy.orm import declarative_base, Session as SqlSession
from sqlalchemy import Column as SqlColumn, String as SqlString, Integer as SqlInteger

from .common import *


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


class RegionCrawler:
    def __init__(self,  storage_engine: SqlEngine):
        self.storage_engine = storage_engine
        Region.create_table(self.storage_engine)

    def crawl(self):
        self._crawl_first_level()   # Provinces, Cities
        self._crawl_other_level(2)  # Districts
        self._crawl_other_level(3)  # Communes

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
            region = Region(
                id=id,
                name=name,
                level=1,
                level_name="Tỉnh, thành phố",
                url=url,
                parent_id=None,
                parent_name=None
            )

            with SqlSession(self.storage_engine) as session:
                if session.get(Region, ident=region.id) == None:
                    session.add(region)
                    session.commit()

        print("DONE: got all administrative level at level 1")

    def _crawl_other_level(self, level: int):
        with SqlSession(self.storage_engine) as session:
            regions_iter = session.query(Region).where(Region.level == level-1)
            regions = list(regions_iter)

        for region in regions:
            url = f"https://{BASE_URL}{region.url}"
            resp = requests.get(url)
            resp.raise_for_status()

            document = etree.HTML(resp.text)
            query = '//div[@id = "sidebar"]//ul/li'

            for elem in document.xpath(query):
                try:
                    url = elem.xpath('.//a/@href')[0]
                    name = elem.xpath('.//a//text()')[0]
                    id = url.split("-")[-1]
                except Exception:
                    print(f"ERROR: {region.__dict__}")
                    continue

                new_region = Region(
                    id=id,
                    name=name,
                    level=level,
                    level_name={2: "Quận, huyện", 3: "Phường, xã"}[level],
                    url=url,
                    parent_id=region.id,
                    parent_name=region.name
                )

                with SqlSession(self.storage_engine) as session:
                    if session.get(Region, ident=new_region.id) == None:
                        session.add(new_region)
                        session.commit()

            print(f"DONE: got all sub-units for {region.name}")
