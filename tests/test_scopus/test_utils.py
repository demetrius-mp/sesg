import asyncio

import httpx


def simulate_network_latency(seconds: float):
    async def inner(request: httpx.Request):
        await asyncio.sleep(seconds)
        return httpx.Response(status_code=200)

    return inner
