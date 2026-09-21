"""RAG v2: chunking + retrieval. Embeddings — через AIProvider (mock или реальный)."""

from __future__ import annotations

from app.config import Settings
from app.db.repo.knowledge import KnowledgeRepo
from app.services.ai.provider import AIProvider


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
        """Разбивает текст на чанки, считает embeddings, сохраняет. Возвращает число чанков."""
        chunks = chunk_text(text, self.settings.rag_chunk_size, self.settings.rag_chunk_overlap)
        if not chunks:
            return 0
        embeddings = await self.provider.embed(chunks)
        repo = KnowledgeRepo(session)
        for chunk, emb in zip(chunks, embeddings, strict=True):
            await repo.add_chunk(owner_id, chunk, emb)
        return len(chunks)

    async def retrieve(self, session, owner_id: int, query: str) -> list[str]:
        """Топ-K релевантных чанков базы знаний владельца. [] если база пуста."""
        rows = await KnowledgeRepo(session).for_owner(owner_id)
        if not rows:
            return []
        embedding = (await self.provider.embed([query]))[0]
        found = await KnowledgeRepo(session).search(
            owner_id, embedding, top_k=self.settings.rag_top_k
        )
        return [row.content for row in found]