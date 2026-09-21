# 📊 MONITORING.md — как следить за ботом и выручкой

Всё, что нужно знать владельцу: бот жив? сколько пользователей? сколько заработано? что с ошибками?

---

## 1. Быстрая проверка «бот онлайн»

**Через /health (если есть доступ к серверу):**
```bash
curl http://localhost:8080/health
# {"status": "ok", "mode": "polling"}  ← норма
```

**Через Telegram (без сервера):**
1. Убедитесь, что бот отвечает на `/start`
2. В @BotFather: `/mybots` → бот → должен быть **включён** (не disabled)
3. В @BotFather → `/mybots` → Bot Settings → не стоит ли webhook на другой сервер
   (при polling — «webhook» должен быть пуст; команда `deleteWebhook` в логах)

**Docker:**
```bash
docker compose ps                      # STATE = Up (healthy)
docker compose logs -f app --tail 50   # «Бот запущен (long polling)» без traceback'ов
```

> Uptime-мониторинг извне (бесплатно): добавьте в UptimeRobot
> монитор типа HTTP на `https://bot.вашдомен.ru/health` — алерт на почту/телеграм,
> если бот упал.

---

## 2. Пользователи и выручка — команда /adminstats

Зайдите в бота под аккаунтом из `ADMIN_IDS` и отправьте:

```
/adminstats
```

Ответ бота:
```
📈 Админ-статистика
Пользователей: 142
С оплатой: 9
Сообщений всего: 3811
Выручка (Stars): 900 ⭐️
```

- **Выручка (Stars)** — сумма всех успешных платежей. 1 ⭐️ ≈ $0.013 при выводе
  (комиссия Fragment). 900 ⭐️ ≈ $11.7
- Норма проверки — раз в день. Пересчёт в MRR: активные Pro × 100 ⭐️ + Business × 250 ⭐️

**Дополнительные запросы** (для аналитики, на SQLite: `sqlite3 data/bot.db`, на PG: psql):
```sql
-- Новые пользователи за 7 дней
SELECT DATE(created_at), COUNT(*) FROM users
WHERE created_at > datetime('now', '-7 days') GROUP BY DATE(created_at);

-- Конверсия Free → платный
SELECT COUNT(DISTINCT p.user_id) * 100.0 / COUNT(*) FROM users u
LEFT JOIN payments p ON p.user_id = u.id AND p.status = 'paid';

-- Топ сообщений в день (нагрузка)
SELECT DATE(created_at), COUNT(*) FROM messages
WHERE role = 'user' GROUP BY DATE(created_at) ORDER BY 1 DESC LIMIT 14;
```

---

## 3. Ошибки — где смотреть и что важно

```bash
docker compose logs app | grep -E "ERROR|CRITICAL" | tail -30
```

| Ошибка в логе | Причина | Что делать |
|---|---|---|
| `LLM retry ... after ...` | провайдер отвечает 429/5xx | норма при пиках; если постоянно — лимиты провайдера исчерпаны |
| `LLM primary failed, switching to fallback` | основной LLM упал | проверьте `LLM_FALLBACK_*`; если нет fallback — задайте |
| `LLM non-retryable error 401` | неверный `LLM_API_KEY` | заменить ключ |
| `Refund API failed` | Stars-возврат отклонён | проверить charge_id; Funds в @BotFather |
| `database is locked` | SQLite на высоких нагрузках | мигрируйте на PostgreSQL (DEPLOY.md §1 prod) |
| `TelegramServerError` | инциденты Telegram | само пройдёт; polling восстановится |

Sentry (опц., 5 минут подключения): `sentry-sdk`, `sentry_sdk.init(dsn=...)` в `app/main.py`
— бесплатные 5k ошибок/мес, трейсбеки с контекстом.

---

## 4. Метрики бизнеса (из docs/MARKETING.md)

| Метрика | Где смотреть | Цель |
|---|---|---|
| Activation (написал ≥1 сообщение) | SQL: users с messages_used > 0 / все users | ≥ 40% |
| Free → Paid | /adminstats: «С оплатой / Пользователей» | ≥ 5% |
| Aha-moment (2+ сообщения за сессию) | SQL: группы сообщений по user_id | ≥ 60% |
| Churn платных | продления в payments за период | < 10%/мес |
| Выручка MRR | /adminstats × периоды | рост w/w |

**Ежедневный чек-лист (1 минута):** `/health` отвечает → `/adminstats` растёт →
в логах нет CRITICAL → ок.
