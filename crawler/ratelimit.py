import asyncio
from datetime import datetime, timedelta


class RateLimiter:
    def __init__(self, requests_per_sec: int):
        self.limit = requests_per_sec
        self.current_count = 0

        # history hold timestamps of successful acquire calls
        # maximum number of element in history is self.limit
        self.history = [datetime.now()]

    @property
    def average_elapsed_time(self) -> float:
        if len(self.history) <= 1:
            return 0.0

    async def acquire(self):
        # Acquire lock
        while self.current_count >= self.limit:
            await asyncio.sleep(1.0 / self.limit)
        self.current_count += 1

        # Lock acquired
        # Check if in cool down period
        if len(self.history) < self.limit:
            current_time = datetime.now()
            self.history.append(current_time)
            return

        # Currently in cool down period
        # Wait untill the period pass
        while True:
            current_time = datetime.now()
            elapsed_time = (current_time - self.history[0]).total_seconds()
            if elapsed_time >= 1:
                self.history.pop(0)
                self.history.append(current_time)
                return
            remain_time = self.history[0] + timedelta(seconds=1) - current_time
            await asyncio.sleep(remain_time.total_seconds())

    async def release(self):
        self.current_count -= 1
        await asyncio.sleep(0.0)

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.release()
