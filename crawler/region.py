import asyncio
import aiohttp
from lxml import etree

import sqlalchemy
from sqlalchemy import Engine as SqlEngine
from sqlalchemy.orm import Session as SqlSession
from sqlalchemy import Column as SqlColumn, String as SqlString, Integer as SqlInteger

from .common import *
from .ratelimit import RateLimiter
from .retry_client import RetryClient


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
        self_repr = f"{self.id} {self.level_name} {self.name}"
        parent_repr = f"{self.parent_id} {_region_levels[self.level]} {self.parent_name}"
        if self.parent_id in ["", None]:
            return self_repr
        return f"{parent_repr} - {self_repr}"


class RegionCrawler:
    def __init__(self,  storage_engine: SqlEngine):
        self.storage_engine = storage_engine
        Region.create_table(self.storage_engine)
        self.limiter = RateLimiter(config.rate_limiter)

    async def crawl(self):
        async with RetryClient(max_retries=config.max_retries,
                               limiter=config.rate_limiter,
                               cookie_jar=aiohttp.DummyCookieJar()) as client:
            await self._crawl_first_level(client)
            await self._crawl_other_level(client, level=2)
            await self._crawl_other_level(client, level=3)

    async def _extract_region_info(self, client: RetryClient, url: str, level: int, parent_region: Region = None):
        # Fetch content from url
        async with client.get(url) as resp:
            if not resp.ok:
                logger.error(
                    f"Failed to get data from {url} with status {resp.status}"
                )
                return
            content = await resp.text()

        # Extract data from response
        document = etree.HTML(content)
        query = '//div[@id = "sidebar"]//ul/li'
        regions = []

        if parent_region != None:
            parent_id = parent_region.id
            parent_name = parent_region.name
        else:
            parent_id = None
            parent_name = None

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
                parent_id=parent_id,
                parent_name=parent_name,
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

    async def _crawl_first_level(self, client: RetryClient):
        url = f"https://{config.domain}"
        await self._extract_region_info(client, url,  level=1)
        logger.success(
            f"Got all regions at level 1 - {_region_levels[1]}"
        )

    async def _crawl_other_level(self, client: RetryClient, level: int):
        with SqlSession(self.storage_engine) as session:
            regions_iter = session.query(Region).where(Region.level == level-1)
            regions = list(regions_iter)

        async def create_task(region):
            url = f"https://{config.domain}{region.url}"
            await self._extract_region_info(client, url, level=level)
            logger.success(f"Got all sub-regions of {region}")

        tasks = [create_task(region) for region in regions]
        await asyncio.gather(*tasks)
