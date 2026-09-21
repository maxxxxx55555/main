from app.db.models.base import Base, utcnow

# Импорты моделей регистрируют таблицы в Base.metadata
from app.db.models.knowledge import KnowledgeBase
from app.db.models.message import Message
from app.db.models.payment import Payment
from app.db.models.user import User

__all__ = ["Base", "KnowledgeBase", "Message", "Payment", "User", "utcnow"]