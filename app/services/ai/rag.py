"""RAG v2: chunking + retrieval через локальное векторное хранилище (SQLite | ChromaDB).

Embeddings:
- VECTOR_STORE=sqlite (по умолчанию) — через AIProvider (mock в dev; embeddings API на платных LLM)
- VECTOR_STORE=chroma — встроенная локальная embedding-модель Chroma (бесплатно,
  работает даже с LLM без embeddings API: Groq/OpenRouter)
"""

from __future__ import annotations

from app.config import Settings
from app.services.ai.provider import AIProvider
from app.services.ai.vector_store import SQLiteVectorStore, build_vector_store


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(text), step):
        chunks.append(text[start : start + chunk_size])
        if start + chunk_size >= len(text):
            break
    return chunks


class RagService:
    def __init__(self, provider: AIProvider, settings: Settings) -> None:
        self.provider = provider
        self.settings = settings

    async def add_text(self, session, owner_id: int, text: str) -> int:
        """Разбивает текст на чанки, сохраняет в векторное хранилище. Возвращает число чанков."""
        chunks = chunk_text(text, self.settings.rag_chunk_size, self.settings.rag_chunk_overlap)
        if not chunks:
            return 0
        store = build_vector_store(session, self.settings)
        return await store.add(owner_id, chunks)

    async def retrieve(self, session, owner_id: int, query: str) -> list[str]:
        """Топ-K релевантных чанков базы знаний владельца. [] если база пуста."""
        store = build_vector_store(session, self.settings)
        if (
            isinstance(store, SQLiteVectorStore)
            and await store.count(owner_id) == 0
        ):
            # Быстрая проверка пустой базы без вызова embeddings
            return []
        return await store.search(owner_id, query, top_k=self.settings.rag_top_k)

    async def forget_owner(self, session, owner_id: int) -> None:
        """Полное удаление базы знаний владельца (для /forget_me)."""
        store = build_vector_store(session, self.settings)
        await store.delete_for_owner(owner_id)