import asyncio
import aiohttp
from lxml import etree
from dataclasses import dataclass

import sqlalchemy
from sqlalchemy.exc import IntegrityError as SqlIntegrityError
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy import Engine as SqlEngine
from sqlalchemy.orm import Session as SqlSession
from sqlalchemy import Column as SqlColumn, String as SqlString

from .common import *
from .ratelimit import RateLimiter
from .region import Region


class Corporate(SqlTableBase):
    __tablename__ = "corporates"
    tax_id = SqlColumn(SqlString, primary_key=True)
    name = SqlColumn(SqlString)
    international_name = SqlColumn(SqlString)
    short_name = SqlColumn(SqlString)
    address = SqlColumn(SqlString)
    phone = SqlColumn(SqlString)
    active_date = SqlColumn(SqlString)
    region_id = mapped_column(ForeignKey(Region.id))
    last_update = SqlColumn(SqlString)

    @classmethod
    def create_table(Self, engine: sqlalchemy.Engine):
        Self.metadata.create_all(engine)


@dataclass
class SearchResult:
    max_page: int = 0
    urls: set[str] = None


class CorporateCrawler:
    def __init__(self,  storage_engine: SqlEngine):
        self.storage_engine = storage_engine
        Corporate.create_table(self.storage_engine)
        self.limiter = RateLimiter(config["rate_limit"])

    async def crawl(self):
        pass

    async def _search_by_region(self, client: aiohttp.ClientSession, region: Region) -> list[str]:
        search_url = f"https://{BASE_URL}{region.url}"
        corporate_urls = []
        current_page = 1
        max_page = 1
        while current_page <= max_page:
            pass

    async def _extract_urls_from_search(self, client: aiohttp.ClientSession, search_url: str) -> SearchResult:
        # Fetch content from url
        async with client.get(search_url) as resp:
            if not resp.ok:
                logger.error(
                    f"Failed to get data from {search_url} with status {resp.status}"
                )
                return
            content = await resp.text()

        # Extract page count
        document = etree.HTML(content)
        query = '//ul[@class = "page-numbers"]//a[@class = "page-numbers"]/text()'
        page_elements = document.xpath(query)
        max_page = 0
        for page_elem in page_elements:
            try:
                page_no = int(page_elem)
            except ValueError:
                page_no = 0
            max_page = max(max_page, page_no)

        # Extract urls
        urls = set()
        query = '//div[@class = "tax-listing"]//div[@data-prefetch != ""]//h3//a/@href'
        elements = document.xpath(query)
        for element in elements:
            url = str(element)
            urls.add(url)

        return SearchResult(max_page=max_page, urls=urls)
