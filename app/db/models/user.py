import datetime as dt

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.dialects.sqlite import INTEGER as SQLITE_INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, utcnow

# SQLite: BIGINT PK не автоинкрементится — подменяем на INTEGER в sqlite-диалекте
BigIntPk = BigInteger().with_variant(SQLITE_INTEGER(), "sqlite")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(16), default="free", nullable=False)
    messages_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    period_reset_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: utcnow() + dt.timedelta(days=30), nullable=False
    )
    tz: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} tg_id={self.tg_id} plan={self.plan} used={self.messages_used}>"