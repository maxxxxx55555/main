"""Health-сервер: /health отвечает в polling-режиме (без Telegram-токена)."""

from __future__ import annotations

import pytest


@pytest.fixture
def webapp():
    return None


async def test_health_endpoint():
    from aiohttp import ClientSession

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
    finally:
        await runner.cleanup()