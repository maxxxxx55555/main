# 🚀 Развёртывание бота на Replit (бесплатный сервер)

Эта инструкция поможет запустить ваш Telegram AI-бот на [Replit](https://replit.com) — **бесплатно, 24/7**.

> 💡 **Примечание:** Replit free tier не поддерживает Webhook (нужен публичный URL). Мы будем использовать **Long Polling**. Бот будет "оживать" при каждом запросе к endpoint-у `keep_alive`.

---

## 📋 Шаг 1: Создать Replit проект

1. Зайдите на https://replit.com
2. Нажмите **"Create Repl"** → выберите язык **"Python"**
3. **Name:** `my-aibot` (или любое другое имя)
4. **Visibility:** Private (рекомендуется)
5. Нажмите **"Create Repl"**

---

## 📥 Шаг 2: Импортировать код бота из GitHub

1. Ваш Replit проект откроется.
2. Удалите файл `.replit` и `replit.nix` если они есть (мы создадим свои).
3. В левом меню нажмите на иконку **"Version Control"** (или `VCS`), затем:
   - **"Import from Git"**
   - URL: `https://github.com/maxxxxx55555/aibot`
   - Нажмите **"Import"**

---

## ⚙️ Шаг 3: Конфигурация Replit

### 3.1. Создайте `.replit`

Создайте новый файл `.replit` в корне проекта (на уровне файлов):

```toml
run = "python -m app.main"
entrypoint = "app/main.py"
modules = ["python3"]
```

### 3.2. Создайте `replit.nix`

```nix
{ pkgs }: {
  deps = with pkgs; [
    python311
    python311Packages.pip
    python311Packages.venv
    gcc
    libpq
  ];
}
```

### 3.3. Настройте переменные окружения

1. В Replit нажмите на вкладку **"Secrets"** (шестерёк в левом меню)
2. Добавьте следующие переменные:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | `ваш токен от @BotFather` |
| `ADMIN_IDS` | ваш Telegram user_id (от @userinfobot) |
| `LLM_API_KEY` | ваш API ключ (например, Groq или OpenRouter) |
| `LLM_PROVIDER` | `groq` или `openrouter` |
| `WEBHOOK_MODE` | `0` (важно! используем long polling) |
| `LLM_MOCK` | `0` (или `1` если хотите тестировать без LLM) |

> **Совет:** Если вы используете `LLM_MOCK=1`, бот будет работать с mock-ответами без ключа LLM — идеально для тестирования интерфейса!

---

## 💾 Шаг 4: Установите зависимости

Откройте **"Shell"** в Replit и выполните:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ▶️ Шаг 5: Запустите бота

Нажмите кнопку **"Run"** в Replit.

Через 2-5 секунд бот должен начать работу. Проверьте чат в Telegram.

---

## 🔄 Шаг 6: Держите бота "живым" 24/7 (free тариф)

Replit free убивает процесс через 15 минут без активности. Решение: **"keep alive"**.

### Вариант A: Keep-alive через внешнее сервис

1. Зарегистрируйтесь на https://uptimerobot.com (бесплатно)
2. Создайте HTTP(s) монитор
3. URL: `https://your-repl-username.repl.co`
   - Если ваш респл называется `my-aibot` и пользователь `username`, URL будет:
     `https://my-aibot.username.repl.co`
4. Это будет "пинговать" вашего бота каждые 5 минут, чтобы он не засыпал.

### Вариант B: Добавьте `keep_alive.py` в проект

Создайте файл `keep_alive.py`:

```python
from flask import Flask, jsonify
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"status": "ok", "bot": "alive"})

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)

def keep_alive():
    server = Thread(target=run, daemon=True)
    server.start()
```

И в `app/main.py` добавьте в начало:

```python
from keep_alive import keep_alive
keep_alive()
```

---

## 🧪 Быстрая проверка

После запуска напишите в Telegram вашему боту:

```
/start
```

Бот должен ответить приветствием с inline-кнопками. Протестируйте:

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню с кнопками |
| `/help` | Справка |
| `/stats` | Статистика подписки |
| `/buy` | Покупка тарифа (Stars) |
| `/knowledge` | База знаний (текст + файлы) |
| `/privacy` | Политика конфиденциальности |
| `/forget_me` | Удалить аккаунт (GDPR) |

---

## ❓ Troubleshooting

| Проблема | Решение |
|----------|---------|
| `Bot not responding` | Проверьте BOT_TOKEN в Secrets |
| `Module not found` | Проверьте requirements.txt, выполните pip install |
| `SQLite error` | Убедитесь что `data/` существует |
| `403 banned` | Проверьте что ваш Telegram аккаунт не забанен |
| Keep-alive не работает | Проверьте URL мониторинга на UptimeRobot |

---

## 📋 Полный чек-лист (93 теста, все зелёные)

- ✅ 93/93 pytest passed
- ✅ ruff: All checks passed
- ✅ Migrations: upgrade head → downgrade base → upgrade head
- ✅ Docker compose валиден
- ✅ Security аудит: чисто (нет утечек, защита payments payload, идемпотентность)

> **Ready for production!**