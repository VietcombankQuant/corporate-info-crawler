import aiohttp
import asyncio

from .ratelimit import RateLimiter


class RetryClient:
    def __init__(self, max_retries: int, limiter: RateLimiter, *args, **kwargs):
        self.max_retries = max_retries
        self.limiter = limiter
        self.args = args
        self.kwargs = kwargs

    async def get(self, url, *args, **kwargs) -> aiohttp.ClientResponse:
        for i in range(self.max_retries):
            async with self.limiter as _:
                async with self.session.get(url, *args, **kwargs) as resp:
                    if resp.ok:
                        return resp
                    timeout = 2**i
                    await asyncio.sleep(timeout)
        return resp

    async def post(self, url, *args, **kwargs) -> aiohttp.ClientResponse:
        for i in range(self.max_retries):
            async with self.limiter as _:
                async with self.session.post(url, *args, **kwargs) as resp:
                    if resp.ok:
                        return resp
                    timeout = 2**i
                    await asyncio.sleep(timeout)
        return resp

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(*self.args, **self.kwargs)
        return await self.session.__aenter__()

    async def __aexit__(self, *args, **kwargs):
        await self.session.__aexit__(*args, **kwargs)
        del self.session
