from app.db.models.base import Base, utcnow  # noqa: F401

# Импорты моделей регистрируют таблицы в Base.metadata
from app.db.models.knowledge import KnowledgeBase  # noqa: E402,F401
from app.db.models.message import Message  # noqa: E402,F401
from app.db.models.payment import Payment  # noqa: E402,F401
from app.db.models.user import User  # noqa: E402,F401

__all__ = ["Base", "KnowledgeBase", "Message", "Payment", "User", "utcnow"]