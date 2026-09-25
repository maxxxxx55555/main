"""RAG: chunking + retrieval через локальное хранилище (SQLite | ChromaDB).

Retrieval-стратегия зависит от VECTOR_STORE:
- sqlite (по умолчанию) — лексический BM25-lite по чанкам владельца (без зависимостей);
- chroma — семантический поиск локальной ONNX-моделью Chroma (бесплатно,
  работает даже с LLM без embeddings API: Groq/OpenRouter).
"""

from __future__ import annotations

from app.config import Settings
from app.services.ai.provider import AIProvider
from app.services.ai.vector_store import build_vector_store


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Чанкинг по границам абзацев с перекрытием (fallback — жёсткая нарезка)."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    step = max(chunk_size - overlap, 1)
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Пытаемся закончить чанк на абзаце, затем на предложении, затем на слове
            for boundary in ("\n\n", "\n", ". ", " "):
                pos = text.rfind(boundary, start + step, end)
                if pos > start:
                    end = pos + len(boundary)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


class RagService:
    def __init__(self, provider: AIProvider, settings: Settings) -> None:
        self.provider = provider
        self.settings = settings

    async def add_text(self, session, owner_id: int, text: str) -> int:
        """Разбивает текст на чанки, сохраняет в хранилище. Возвращает число чанков."""
        chunks = chunk_text(text, self.settings.rag_chunk_size, self.settings.rag_chunk_overlap)
        if not chunks:
            return 0
        store = build_vector_store(session, self.settings)
        return await store.add(owner_id, chunks)

    async def retrieve(self, session, owner_id: int, query: str) -> list[str]:
        """Топ-K релевантных чанков базы знаний владельца. [] если база пуста."""
        store = build_vector_store(session, self.settings)
        if await store.count(owner_id) == 0:
            return []  # быстрый выход: не тратим ресурсы на пустую базу
        return await store.search(owner_id, query, top_k=self.settings.rag_top_k)

    async def forget_owner(self, session, owner_id: int) -> None:
        """Полное удаление базы знаний владельца (для /forget_me)."""
        store = build_vector_store(session, self.settings)
        await store.delete_for_owner(owner_id)