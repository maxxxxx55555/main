import datetime as dt

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def utcnow() -> dt.datetime:
    """Naive UTC — единое представление времени для SQLite и PostgreSQL."""
    return dt.datetime.now(dt.UTC).replace(tzinfo=None)


def to_naive_utc(value: dt.datetime | None) -> dt.datetime | None:
    """Нормализация значения из БД (timestamptz на PG отдаёт aware)."""
    if value is not None and value.tzinfo is not None:
        return value.astimezone(dt.UTC).replace(tzinfo=None)
    return value