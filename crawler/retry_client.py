import aiohttp
import asyncio
from contextlib import asynccontextmanager

from .common import logger, config
from .ratelimit import RateLimiter


class RetryClient:
    def __init__(self, max_retries: int, limiter: RateLimiter, *args, **kwargs):
        self.max_retries = max_retries
        self.limiter = limiter
        self.args = args
        self.kwargs = kwargs

    @asynccontextmanager
    async def get(self, url, *args, **kwargs) -> aiohttp.ClientResponse:
        for i in range(self.max_retries):
            domain = config.domain
            full_url = f"https://{domain}{url}"
            async with self.limiter as _:
                async with self.session.get(full_url, *args, **kwargs) as resp:
                    if resp.ok or (i == self.max_retries - 1):
                        yield resp
                        return
            logger.warning(
                f"Retry {i+1}/{self.max_retries} for {full_url} failed with status {resp.status}"
            )
            config.remove_gateway(domain)
            timeout = 2**i
            await asyncio.sleep(timeout)

        # Max retries reached => return errors
        yield resp
        return

    @asynccontextmanager
    async def post(self, url, *args, **kwargs) -> aiohttp.ClientResponse:
        for i in range(self.max_retries):
            domain = config.domain
            full_url = f"https://{config.domain}{url}"
            async with self.limiter as _:
                async with self.session.post(full_url, *args, **kwargs) as resp:
                    if resp.ok or (i == self.max_retries-1):
                        yield resp
                        return
            logger.warning(
                f"Retry {i+1}/{self.max_retries} for {full_url} failed with status {resp.status}"
            )
            config.remove_gateway(domain)
            timeout = 2**i
            await asyncio.sleep(timeout)

        # Max retries reached => return errors
        yield resp
        return

    async def __aenter__(self):
        session = aiohttp.ClientSession(*self.args, **self.kwargs)
        self.session = await session.__aenter__()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.session.__aexit__(*args, **kwargs)
        del self.session
