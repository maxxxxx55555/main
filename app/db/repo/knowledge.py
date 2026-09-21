import struct

from sqlalchemy import delete, select

from app.db.models.knowledge import KnowledgeBase, cosine_similarity, decode_vector
from app.db.repo.base import BaseRepo


class KnowledgeRepo(BaseRepo[KnowledgeBase]):
    model = KnowledgeBase

    async def add_chunk(self, owner_id: int, content: str, embedding: list[float]) -> KnowledgeBase:
        chunk = KnowledgeBase(
            owner_id=owner_id,
            content=content,
            embedding=struct.pack(f"<{len(embedding)}f", *embedding),
        )
        self.session.add(chunk)
        await self.session.flush()
        return chunk

    async def for_owner(self, owner_id: int) -> list[KnowledgeBase]:
        result = await self.session.execute(
            select(KnowledgeBase).where(KnowledgeBase.owner_id == owner_id)
        )
        return list(result.scalars().all())

    async def search(self, owner_id: int, query_embedding: list[float], top_k: int = 5) -> list[KnowledgeBase]:
        """ANN-поиск. SQLite/dev: линейный перебор с косинусной близостью.

        PostgreSQL/prod: заменяется на pgvector HNSW (см. ARCHITECTURE.md §3);
        сигнатура и результат — идентичны.
        """
        rows = await self.for_owner(owner_id)
        scored = []
        q = query_embedding
        for row in rows:
            vec = decode_vector(row.embedding)
            scored.append((cosine_similarity(q, vec), row))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [row for score, row in scored[:top_k]]

    async def delete_for_owner(self, owner_id: int) -> int:
        result = await self.session.execute(
            delete(KnowledgeBase).where(KnowledgeBase.owner_id == owner_id)
        )
        return result.rowcount or 0