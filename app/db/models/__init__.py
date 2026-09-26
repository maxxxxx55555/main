from app.db.models.base import Base, utcnow

# Импорты моделей регистрируют таблицы в Base.metadata
from app.db.models.knowledge import KnowledgeBase
from app.db.models.lead import Feedback, Lead
from app.db.models.chat import ChatMemberActivity, ChatSettings
from app.db.models.message import Message
from app.db.models.payment import Payment
from app.db.models.user import User

__all__ = ["Base", "ChatMemberActivity", "ChatSettings", "Feedback", "KnowledgeBase", "Lead", "Message", "Payment", "User", "utcnow"]