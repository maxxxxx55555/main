# 🚀 DEPLOY.md — продакшн-деплой на VPS за €5/мес

Путь: Hetzner/DigitalOcean → Docker → бот онлайн. Время: ~20 минут.

---

## 1. Аренда сервера

**Hetzner** (рекомендую по цене/качеству, €4-5/мес):
1. https://www.hetzner.com/cloud → Create Server
2. Локация: Nuremberg/Helsinki; **CX22** (2 vCPU, 4GB — с запасом) или самый дешёвый CX11-класс
3. OS: **Ubuntu 24.04**
4. После создания: скопируйте публичный IP

**DigitalOcean** ($6/мес): Ubuntu 24.04, Basic Droplet 1GB минимум.

**Настройка SSH** (локальный терминал):
```bash
ssh root@ВАШ_IP        # первый вход (пароль из панели или ваш ключ)
```

---

## 2. Установка Docker + код

На сервере:
```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
```

Либо одной командой (в репозитории есть автоматический скрипт):
```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> ai-employee
cd ai-employee
bash deploy.sh
```

---

## 3. Настройка .env

```bash
cp .env.example .env
nano .env
```

Обязательные для прода значения:

```env
BOT_TOKEN=токен_от_BotFather
LLM_API_KEY=ключ_GLM_или_OpenAI
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4   # или OpenAI
ADMIN_IDS=ваш_telegram_id
POSTGRES_PASSWORD=длинная_случайная_строка          # openssl rand -hex 16
```

**Режим приёма апдейтов:**

| Вариант | WEBHOOK_MODE | Нужен домен? | Кому подходит |
|---|---|---|---|
| Long polling | `0` | нет | старт, до ~1k пользователей |
| Webhook | `1` | да | прод, масштабирование |

Стартуйте с polling (`WEBHOOK_MODE=0`) — меньше движений. Webhook добавите по §5.

---

## 4. Запуск

```bash
docker compose --profile prod up -d --build
docker compose --profile prod exec -T app alembic upgrade head   # миграции
curl http://localhost:8080/health                                # {"status": "ok"}
docker compose logs -f app                                       # смотреть логи
```

Готово — бот онлайн 24/7. Проверка: напишите боту `/start` в Telegram.

**Полезное:**
```bash
docker compose ps                      # статус контейнеров
docker compose restart app             # перезапуск
docker compose --profile prod down     # остановка
docker compose logs -f app --tail 100  # последние логи
```

---

## 5. Домен + webhook (опционально, для HTTPS)

Telegram требует HTTPS для webhook. Бесплатный TLS — Caddy (авто Let's Encrypt).

1. Купите дешёвый домен (или бесплатный: duckdns.org), создайте A-запись `bot.вашдомен.ru → IP сервера`
2. `docker-compose.override.yml` с Caddy:
```yaml
services:
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddydata:/data
volumes:
  caddydata:
```
3. `Caddyfile`:
```
bot.вашдомен.ru {
    reverse_proxy app:8080
}
```
4. В `.env`:
```env
WEBHOOK_MODE=1
WEBHOOK_BASE_URL=https://bot.вашдомен.ru
WEBHOOK_SECRET_TOKEN=<openssl rand -hex 32>
```
5. `docker compose --profile prod up -d --build && docker compose exec app alembic upgrade head`

Проверка webhook: `curl https://bot.вашдомен.ru/health` → `{"status":"ok"}`

---

## 6. Обновления и бэкапы

**Обновление кода:**
```bash
git pull
docker compose --profile prod up -d --build
docker compose --profile prod exec -T app alembic upgrade head
```

**Бэкап PostgreSQL** (добавьте в cron: `crontab -e`):
```bash
0 4 * * * docker compose --profile prod exec -T postgres pg_dump -U bot aiemployee | gzip > /root/backups/db_$(date +\%F).sql.gz
```

**Безопасность:**
- `ufw allow 22,80,443 && ufw enable` — закрыть всё лишнее
- SSH по ключу, `PasswordAuthentication no` в `/etc/ssh/sshd_config`
- `.env` никогда не в git; `chmod 600 .env`

---

## 7. Стоимость и точки отказа

| Статья | Цена |
|---|---|
| VPS Hetzner CX22 | €4-5/мес |
| Домен | ~$10/год (опц.) |
| LLM (GLM, ~50k сообщ/мес) | $3-10/мес |
| Telegram Stars комиссия ~30%+ ~45% вывод | учтено в ценах тарифов |
| **Итого fixed** | **~€8-15/мес** |

Точка отказа №1 — доступность LLM-провайдера: настроен fallback (`.env: LLM_FALLBACK_*`).
Точка отказа №2 — VPS: бэкап БД по cron, быстрый перенос — `docker compose up` на новом сервере.
