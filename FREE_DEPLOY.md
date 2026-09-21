# 💸 FREE_DEPLOY.md — хостинг за $0/мес

Бот работает на бесплатном стеке: **SQLite** (файл) + **Groq/OpenRouter** (бесплатные LLM) +
**ChromaDB** (локальные векторы). Ниже два пути запуска без оплаты сервера.

| Путь | Надёжность | Первый ответ после сна | Для кого |
|---|---|---|---|
| **А: свой ПК + Cloudflare Tunnel** | высокая (пока включён ПК) | мгновенно | старт, тесты, первые 50-100 юзеров |
| **Б: Render.com Free** | средняя (засыпает) | 30-60 сек после 15 мин простоя | демонстрация, лёгкий прод |

> Честно: $0-хостинг ≠ полноценный прод. Как только появятся платные пользователи —
> VPS за €5 (см. `DEPLOY.md`) снимет все ограничения.

---

## Подготовка (общая для обоих путей)

1. Токен бота: @BotFather → `/newbot` (см. `QUICK_START.md` шаг 1)
2. Ключ LLM — бесплатно:
   - **Groq**: https://console.groq.com/keys → Create API Key (щедрый бесплатный tier, очень быстрый)
   - **OpenRouter**: https://openrouter.ai/keys → Create Key (модели `...:free`)
3. В `.env`:
   ```env
   BOT_TOKEN=ваш_токен
   LLM_PROVIDER=groq            # или openrouter
   LLM_API_KEY=ваш_ключ
   # БД и векторы — по умолчанию уже бесплатные:
   # DATABASE_URL=sqlite+aiosqlite:///./data/bot.db
   # VECTOR_STORE=chroma        # опционально; sqlite — тоже бесплатно
   ADMIN_IDS=ваш_telegram_id
   ```
4. Установка и проверка локально:
   ```bash
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt     # Linux/macOS: .venv/bin/pip install -r requirements.txt
   .venv\Scripts\pytest -q                           # 37 passed
   ```

---

## ПУТЬ А: локальный ПК + Cloudflare Tunnel (бесплатный HTTPS для webhook)

Cloudflare Tunnel даёт публичный HTTPS-URL без домена, без порт-форвардинга, без оплаты.

### А1. Запуск бота локально в webhook-режиме

В `.env`:
```env
WEBHOOK_MODE=1
WEBHOOK_BASE_URL=https://URL_ПОЛУЧИТЕ_НА_ШАГЕ_А3
WEBHOOK_SECRET_PATH=tg-webhook
WEBHOOK_SECRET_TOKEN=любая_длинная_случайная_строка
WEBAPP_PORT=8080
```
> Можно сначала выполнить А2-А3, получить URL, и только потом запускать бота — так проще.

### А2. Установка cloudflared

- **Windows**: скачать `cloudflared-windows-amd64.exe` с
  https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  → переименовать в `cloudflared.exe`, положить в папку проекта
- **Linux**: `wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared`
- **macOS**: `brew install cloudflared`

Регистрация не обязательна — quick-туннель работает без аккаунта.

### А3. Поднять туннель (1 команда)

Терминал №2 (пока бот запущен в №1):
```bash
cloudflared tunnel --url http://localhost:8080
```

Вывод:
```
+--------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at:            |
|  https://random-words-here-1234.trycloudflare.com            |
+--------------------------------------------------------------+
```

Скопируйте URL — он публичный и HTTPS, именно то, что нужно Telegram.

⚠️ **Ограничение quick-туннеля**: URL меняется при каждом перезапуске cloudflared.
- **Просто**: обновлять `WEBHOOK_BASE_URL` в `.env` и перезапускать бота
- **Стабильно** (бесплатно, нужен только e-mail): dash.cloudflare.com → Zero Trust →
  Networks → Tunnels → Create tunnel — постоянное имя `имя.cfargotunnel.com`

### А4. Подставить URL и перезапустить

1. Остановите бота (Ctrl+C)
2. В `.env`: `WEBHOOK_BASE_URL=https://random-words-here-1234.trycloudflare.com`
3. `.venv\Scripts\python -m app.main` → в логах: `Webhook установлен: https://.../tg-webhook`

### А5. Проверка

- Браузер: `https://random-words-...trycloudflare.com/health` → `{"status":"ok","mode":"webhook"}`
- Telegram: `/start` → приветствие ✅
- ПК в сон = бот спит. Для 24/7 — Always-on ПК или путь Б.

---

## ПУТЬ Б: Render.com Free Tier

### Б1. Код на GitHub
```bash
git remote add origin https://github.com/ВАШ_ЛОГИН/ai-employee.git
git push -u origin main
```

### Б2. Создание сервиса
1. https://render.com → Sign Up (через GitHub) → **New +** → **Background Worker**
   (не Web Service — бот ходит в Telegram сам через polling, HTTP-порт не нужен)
2. Подключите репозиторий, настройки:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m app.main`
   - **Instance Type**: Free
3. **Environment** → добавить переменные:
   ```
   BOT_TOKEN        = токен_BotFather
   LLM_PROVIDER     = groq
   LLM_API_KEY      = ключ_groq
   ADMIN_IDS        = ваш_telegram_id
   DATABASE_URL     = sqlite+aiosqlite:///./data/bot.db
   WEBHOOK_MODE     = 0
   LOG_LEVEL        = INFO
   ```
4. **Create Resource** → деплой 3-5 минут → в логах: «Бот запущен (long polling)»

### Б3. Честные ограничения Free Tier

| Ограничение | Что значит | Митигация |
|---|---|---|
| Sleep у **Web Services** после 15 мин простоя → 30-60 сек на пробуждение первого ответа | задержка ответа клиентам | выбирайте **Background Worker** — polling сам держит активность |
| Рестарты инстанса (~раз в неделю и при деплоях) | короткий простой 30-60 сек | приемлемо для MVP |
| **Ephemeral диск**: `data/bot.db` и `chroma_db/` стираются при рестарте/деплое | обнуляются лимиты и база знаний | см. Б4 |
| 750 часов/мес | хватает на один сервис 24/7 | — |

### Б4. Персистентность на Free — честные варианты

1. **Минимальный MVP (рекомендую на старт)**: принять ephemeral-диск. Обнуление
   free-лимитов (30 сообщ/30 дней) некритично — они и так скользящие.
2. **Бесплатная внешняя БД**: Supabase/Neon free → `DATABASE_URL=postgresql+asyncpg://...`
   — пользователи, платежи и лимиты переживают рестарты.
3. **База знаний**: при ephemeral-диске Chroma тоже стирается — храните исходные
   документы у себя и перезагружайте через `/knowledge` (1 сообщение), либо используйте
   вариант 2 + `VECTOR_STORE=sqlite` с pgvector-миграцией позже.
4. Render Persistent Disk — только на платных планах.

### Б5. Обновления
```bash
git push origin main    # Render задеплоит автоматически
```

---

## Итоговая таблица расходов

| Статья | Путь А | Путь Б |
|---|---|---|
| Хостинг | $0 (ваш ПК) | $0 (Free Tier) |
| HTTPS/домен | $0 (Cloudflare Tunnel) | $0 (не нужен для polling) |
| LLM | $0 (Groq/OpenRouter free) | $0 |
| Векторная БД | $0 (ChromaDB локально) | $0 |
| PostgreSQL | $0 (SQLite локально) | $0 (или Supabase free) |
| **Итого** | **$0/мес** | **$0/мес** |

Когда пойдут платные пользователи → `DEPLOY.md` (VPS €5/мес, персистентный диск, webhook 24/7).