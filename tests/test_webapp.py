"""Health-сервер: /health отвечает в polling-режиме (без Telegram-токена)."""

from __future__ import annotations

import pytest


@pytest.fixture
def webapp():
    return None


async def test_health_endpoint():
    from aiohttp import ClientSession

    from app import __version__
    from app.main import start_webapp

    runner = await start_webapp("127.0.0.1", 18099, None, None, None)
    try:
        async with (
            ClientSession() as http,
            http.get("http://127.0.0.1:18099/health") as resp,
        ):
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "ok"
            assert data["mode"] == "polling"
            assert data["version"] == __version__
            assert isinstance(data["uptime_s"], int) and data["uptime_s"] >= 0
    finally:
        await runner.cleanup()


async def test_health_concurrent_requests():
    """Health-эндпоинт отдаёт 200 при параллельных запросах (профиль LB)."""
    import asyncio

    from aiohttp import ClientSession

    from app.main import start_webapp

    runner = await start_webapp("127.0.0.1", 18098, None, None, None)
    try:
        async with ClientSession() as http:

            async def call() -> int:
                async with http.get("http://127.0.0.1:18098/health") as resp:
                    return resp.status

            statuses = await asyncio.gather(*[call() for _ in range(5)])
        assert statuses == [200] * 5
    finally:
        await runner.cleanup()