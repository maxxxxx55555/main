"""База знаний (RAG).

Чанки текста хранятся в `knowledge_base`; поиск:
- SQLite (по умолчанию, $0): лексический BM25-lite в Python — без внешних сервисов
  (см. services/ai/scoring.py);
- ChromaDB (`VECTOR_STORE=chroma`): семантический поиск локальной ONNX-моделью
  (работает и с LLM без embeddings API: Groq/OpenRouter) — см. services/ai/vector_store.py.

При масштабировании — PostgreSQL + pgvector (docs/ARCHITECTURE.md §3, §10).
"""

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, Text
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
    tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
