import datetime as dt

from sqlalchemy import delete, select

from app.db.models.base import utcnow
from app.db.models.message import Message
from app.db.repo.base import BaseRepo


class MessageRepo(BaseRepo[Message]):
    model = Message

    async def add_message(self, user_id: int, role: str, content: str, tokens: int = 0) -> Message:
        msg = Message(user_id=user_id, role=role, content=content, tokens=tokens)
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def recent(self, user_id: int, limit: int) -> list[Message]:
        """Последние N сообщений в хронологическом порядке (окно контекста)."""
        result = await self.session.execute(
            select(Message)
            .where(Message.user_id == user_id, Message.role != "system")
            .order_by(Message.id.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        rows.reverse()
        return rows

    async def delete_history(self, user_id: int) -> int:
        result = await self.session.execute(delete(Message).where(Message.user_id == user_id))
        return result.rowcount or 0

    async def purge_older_than(self, days: int) -> int:
        """Retention-очистка (§9.4): удаляем сообщения старше N дней."""
        cutoff = utcnow() - dt.timedelta(days=days)
        result = await self.session.execute(delete(Message).where(Message.created_at < cutoff))
        return result.rowcount or 0