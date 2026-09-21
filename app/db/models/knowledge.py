"""База знаний (RAG v2).

SQLite (dev): embedding — BLOB (float32 little-endian), ANN = линейный
перебор с косинусной близостью в Python (приемлемо на dev-объёмах).
PostgreSQL (prod): колонка заменяется на pgvector `vector(EMBEDDING_DIM)`
с HNSW-индексом — см. docs/ARCHITECTURE.md §3. Код сервисов одинаков.
"""

import datetime as dt
import struct

from sqlalchemy import BLOB, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, utcnow
from app.db.models.user import BigIntPk


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        BigIntPk, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[bytes] = mapped_column(BLOB, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


def encode_vector(values: list[float]) -> bytes:
    return struct.pack(f"<{len(values)}f", *values)


def decode_vector(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"<{n}f", blob[: n * 4]))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)