import asyncio
import aiohttp
from lxml import etree
from dataclasses import dataclass
from typing import Union

import sqlalchemy
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
    rep_person = SqlColumn(SqlString)
    company_type = SqlColumn(SqlString)
    industry = SqlColumn(SqlString)
    address = SqlColumn(SqlString)
    phone = SqlColumn(SqlString)
    active_date = SqlColumn(SqlString)
    region_id = mapped_column(ForeignKey(Region.id))
    status = SqlColumn(SqlString)
    last_update = SqlColumn(SqlString)

    @classmethod
    def create_table(Self, engine: sqlalchemy.Engine):
        Self.metadata.create_all(engine)

    def __repr__(self) -> str:
        return f'Tax ID: "{self.tax_id}", Name: "{self.name}"'


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
        with SqlSession(self.storage_engine) as session:
            query = session.query(Region).where(Region.level == 3)
            regions = [region for region in query]
            logger.success(
                f"Got {len(regions)} regions at level 3 from database"
            )

        cookie_jar = aiohttp.DummyCookieJar()
        async with aiohttp.ClientSession(cookie_jar=cookie_jar) as client:
            for region in regions:
                urls = await self._search_by_region(client, region)
                tasks = [
                    self._extract_corporate_info(client, url, region) for url in urls
                ]
                corporates = await asyncio.gather(*tasks)

                record_counter = 0
                with SqlSession(self.storage_engine) as sql_session:
                    for corporate in corporates:
                        if corporate != None and sql_session.get(Corporate, ident=corporate.tax_id) == None:
                            sql_session.add(corporate)
                            record_counter += 1
                    sql_session.commit()

                logger.success(
                    f'Added {record_counter} corporate infor records '
                    f'in region {region} into "corporates table"'
                )

    _corporate_xpath_queries = {
        "tax_id": '//table[@class = "table-taxinfo"]//td[@itemprop="taxID"]/span/text()',
        "name": '//table[@class = "table-taxinfo"]//th[@itemprop="name"]/span/text()',
        "rep_person": '//table[@class = "table-taxinfo"]//td/span[@itemprop="name"]/a/text()',
        "company_type": '//table[@class = "table-taxinfo"]//td/i[contains(@class, "fa-building")]/parent::td/following-sibling::td/a/text()',
        "industry": '//h3[contains(text(), "Ngành nghề kinh doanh")]//following-sibling::table//td/strong/a/text()',
        "address": '//table[@class = "table-taxinfo"]//td[@itemprop="address"]/span/text()',
        "phone": '//table[@class = "table-taxinfo"]//td[@itemprop="telephone"]/span/text()',
        "active_date": '//table[@class = "table-taxinfo"]//td/i[contains(@class, "fa-calendar")]/parent::td/following-sibling::td/span/text()',
        "status": '//table[@class = "table-taxinfo"]//td/i[contains(@class, "fa-info")]/parent::td/following-sibling::td/a/text()',
        "last_update": '//table[@class = "table-taxinfo"]//button[@data-target = "#modal-update"]/preceding-sibling::em/text()',
    }

    async def _extract_corporate_info(self, client: aiohttp.ClientSession, url: str, region: Region) -> Union[Corporate, None]:
        # Fetch corporate data from url
        full_url = f"https://{BASE_URL}{url}"
        async with client.get(full_url) as resp:
            if not resp.ok:
                logger.error(
                    f"Failed to get corporate data from {url} with status {resp.status}"
                )
                return None
            content = await resp.text()

        # Extract data from response
        document = etree.HTML(content)
        corporate = Corporate()
        corporate.region_id = region.id

        for field_name, query in self._corporate_xpath_queries.items():
            results = document.xpath(query)
            if len(results) != 0:
                field_value = " ".join(results)
                corporate.__dict__[field_name] = field_value

        logger.success(
            f"Extracted corporate information item {corporate} from {url}"
        )

        return corporate

    async def _search_by_region(self, client: aiohttp.ClientSession, region: Region) -> set[str]:
        search_url = f"https://{BASE_URL}{region.url}"
        corporate_urls = set()
        current_page = 1
        max_page = 1

        while current_page <= max_page:
            search_result = await self._extract_search_result(client, search_url, params={"page": current_page})
            max_page = max(search_result.max_page, max_page)
            current_page += 1
            corporate_urls.update(search_result.urls)

        return corporate_urls

    async def _extract_search_result(self, client: aiohttp.ClientSession, search_url: str, params: dict = None) -> SearchResult:
        # Fetch content from url
        async with client.get(search_url, params=params) as resp:
            if not resp.ok:
                logger.error(
                    f"Failed to get data from {search_url} with status {resp.status}"
                )
                return SearchResult(max_page=0, urls=set())
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
