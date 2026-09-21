# 🤖 AI-Сотрудник — Telegram AI-ассистент для малого бизнеса

Telegram-бот «AI-Сотрудник»: отвечает клиентам вашего бизнеса 24/7, квалифицирует
лидов, записывает на консультации и отвечает по вашей базе знаний. Монетизация —
Telegram Stars (Freemium / Pro / Business).

> ⚡ **Быстрый старт:** [`QUICK_START.md`](QUICK_START.md) — бот работает за 5 минут, без Docker
> 🚀 **Деплой на VPS:** [`DEPLOY.md`](DEPLOY.md) · 📊 **Мониторинг:** [`MONITORING.md`](MONITORING.md)
> ✅ **Чек-лист запуска:** [`CHECKLIST.md`](CHECKLIST.md) · 📣 **Маркетинг:** [`docs/LAUNCH_MATERIALS.md`](docs/LAUNCH_MATERIALS.md)
> 📚 Продукт и архитектура: [`docs/PRD.md`](docs/PRD.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/MARKETING.md`](docs/MARKETING.md)

## Возможности MVP (v1)

- ✅ Диалог с LLM от лица вашего бизнеса (OpenAI-совместимый API: GLM / OpenAI / прокси)
- ✅ База знаний (RAG): загрузите FAQ и цены — бот отвечает строго по ним (Pro/Business)
- ✅ Freemium-лимиты: атомарное списание, скользящие 30 дней, ленивый сброс
- ✅ Оплата Telegram Stars: invoice → pre_checkout → идемпотентная активация
- ✅ Admin: статистика, возвраты (`/refund`)
- ✅ Приватность: `/forget_me` удаляет все данные пользователя (CASCADE)
- ✅ Отказоустойчивость: ретраи LLM, fallback-провайдер, возврат лимита при сбое
- ✅ Mock-режим LLM: полный цикл разработки/тестов без внешних ключей

## Быстрый старт (2 минуты, без ключей)

```bash
git clone <repo> && cd bot
python -m venv .venv
.venv\Scripts\pip install -e .[dev]      # Windows; Linux/macOS: .venv/bin/pip ...
copy .env.example .env                   # вписать BOT_TOKEN от @BotFather
.venv\Scripts\pytest -q                  # тесты: зелёные без LLM-ключа
.venv\Scripts\python -m app.main         # запуск бота (LLM в mock-режиме)
```

Без `LLM_API_KEY` бот работает на **MockProvider** — отвечает детерминированными
заглушками. Для реальных ответов впишите ключ:

```env
LLM_API_KEY=ваш_ключ
# GLM: https://open.bigmodel.cn/api/paas/v4
# OpenAI: https://api.openai.com/v1
```

## Тарифы

| Тариф | Цена | Лимит/30 дней | Функции |
|---|---|---|---|
| Free | 0 ⭐️ | 30 | базовый чат |
| Pro | 100 ⭐️ | 500 | + база знаний (RAG) |
| Business | 250 ⭐️ | 2000 | + RAG, приоритет |

Цены/лимиты переопределяются через `.env` (`PRO_PRICE_STARS`, `PRO_LIMIT`, …) — без релиза кода.

## Архитектура

Модульный монолит со строгой слоистостью:

```
bot/handlers (Telegram I/O) → services (бизнес-логика) → db/repo (доступ к данным)
```

- **Стек:** Python 3.11+, aiogram 3, SQLAlchemy 2 (async), SQLite (dev) / PostgreSQL 16 + pgvector (prod), Redis (опц.)
- **LLM:** единый интерфейс провайдера, base_url конфигурируется → смена модели без правок кода
- **Платежи:** идемпотентность по `telegram_payment_charge_id` (UNIQUE)
- **Лимиты:** атомарный `UPDATE … WHERE messages_used < limit` — гонки исключены

Подробно (схема БД, поток Stars, edge cases, безопасность, масштабирование):
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Docker

```bash
# Dev-профиль: только бот + SQLite
docker compose up -d --build

# Prod-профиль: + PostgreSQL (pgvector) + Redis
# DATABASE_URL=postgresql+asyncpg://bot:secret@postgres:5432/aiemployee
# REDIS_URL=redis://redis:6379/0
docker compose --profile prod up -d --build
```

## Тесты

```bash
pytest -q          # unit: лимиты, биллинг, RAG, контекст, провайдер
ruff check app     # линтер
```

Тесты используют SQLite in-memory и MockProvider — без сети и секретов.

## Roadmap

- [ ] v1.1: alembic-миграции, webhook-режим (aiohttp + secret_token), summary длинных диалогов
- [ ] v2: аналитика (конверсия воронки), pgvector HNSW, экспорт лидов, реферальная программа
- [ ] v3: white label, API для Enterprise, автоматизации (вебхуки → CRM)

## Структура

```
app/
├── main.py                  # сборка и запуск (polling, graceful shutdown)
├── config.py                # pydantic-settings — единственный источник конфигурации
├── db/                      # движок, модели (User, Message, Payment, KnowledgeBase), repo
├── services/
│   ├── ai/                  # provider (OpenAI-compat | mock), prompt, context, rag
│   ├── billing/             # каталог тарифов, Telegram Stars (§5)
│   └── limits/              # атомарное списание, скользящий период
├── bot/                     # роутер, middlewares (db/user/throttling), handlers, keyboards
└── utils/                   # логирование без секретов
```
