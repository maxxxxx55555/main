"""Логирование без секретов: в логи не попадает содержимое сообщений."""

from __future__ import annotations

import logging
import sys

from app.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Шумные библиотеки — на WARNING
    for noisy in ("aiogram.event", "asyncio", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def mask_secret(value: str) -> str:
    """Маскирование секретов для безопасного логирования."""
    if not value:
        return ""
    return f"{value[:4]}…{value[-4:]}" if len(value) > 8 else "***"