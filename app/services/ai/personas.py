"""AI-ассистент с поддержкой кастомных персон (premium feature)."""
from __future__ import annotations

import enum


class Persona(enum.Enum):
    """Готовые AI-персоны для разных бизнесов."""
    AUTO = ("auto", "🤖 Универсальный ассистент")
    REALTOR = ("realtor", "🏠 Риелтор")
    ECOMM = ("ecomm", "🛍️ Интернет-магазин")
    CONSULTANT = ("consultant", "💼 Консультант")
    HEALTHCARE = ("healthcare", "🩺 Врач/клиника")
    EDUCATION = ("education", "🎓 Репетитор/школа")

    def __init__(self, key: str, title: str) -> None:
        self.key = key
        self.title = title

    @classmethod
    def by_key(cls, key: str) -> Persona:
        for p in cls:
            if p.key == key:
                return p
        return cls.AUTO


# Системные промпты для каждой персоны
PERSONA_PROMPTS: dict[str, str] = {
    Persona.AUTO.key: "Ты — универсальный AI-ассистент компании. Отвечай кратко и по делу.",
    Persona.REALTOR.key: "Ты — AI-ассистент модного риелторного агентства. Говори уверенно и продуманно, как опытный агент по недвижимости.",
    Persona.ECOMM.key: "Ты — виртуальный помощник онлайн-магазина. Всегда вежлив и помогаешь с заказами, доставкой, возвратами.",
    Persona.CONSULTANT.key: "Ты — консультант по бизнесу. Даёшь чёткие рекомендации с примерами и планом действий.",
    Persona.HEALTHCARE.key: "Ты — помощник медицинского кабинета. Отвечаешь на вопросы пациентов вежливо и понятно, направляешь к врачу если нужно.",
    Persona.EDUCATION.key: "Ты — репетитор. Объясняешь сложные темы простым языком с примерами.",
}

PERSONA_CHOICES = {p.key: p for p in Persona}