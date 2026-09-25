# ✅ CHECKLIST — перед запуском на пользователей

## Проверки текущего состояния (25.09.2026)

- [x] `.venv\Scripts\python.exe -m pytest -q` → **91 passed**
- [x] `.venv\Scripts\python.exe -m ruff check app migrations tests` → **All checks passed**
- [x] `.venv\Scripts\python.exe -m compileall -q app migrations tests` → без ошибок компиляции
- [x] Alembic на отдельной SQLite-БД: `upgrade head → downgrade base → upgrade head` → все три команды завершились с кодом 0
- [x] Миграции применяются автоматически при старте (`app.db.base.run_migrations`), повторный запуск безопасен
- [x] Локальный `HEAD` и `origin/main` синхронизируются после финального коммита
- [x] В tracked-файлах нет `.env`, рабочей БД, Chroma-данных или `.venv`

## Локально (5 минут)

- [ ] `pytest -q` → **91 passed**
- [ ] `.venv/Scripts/python -m app.main` стартует, в логе нет traceback
- [ ] `curl http://localhost:8080/health` → `{"status": "ok"}`
- [ ] В Telegram: `/start` → приветствие с меню

## Конфигурация .env

- [ ] `BOT_TOKEN` — токен от @BotFather (не от чужого бота!)
- [ ] `LLM_API_KEY` — вписан и **проверен** (без него ответы-заглушки!)
  - Проверка: напишите боту вопрос — ответ НЕ должен начинаться с `[MOCK]`
- [ ] `ADMIN_IDS` — ваш Telegram ID (узнать: @userinfobot)
- [ ] `POSTGRES_PASSWORD` — если prod-профиль (случайная строка, не "password")

## Прод-деплой (DEPLOY.md)

- [ ] VPS создан, Docker установлен (`docker compose version`)
- [ ] `.env` на сервере заполнен, `chmod 600 .env`
- [ ] `docker compose --profile prod up -d --build` — без ошибок
- [ ] `docker compose exec -T app alembic upgrade head` — миграции применены
- [ ] `curl http://localhost:8080/health` → ok
- [ ] UptimeRobot (или аналог) следит за `/health` — алерты включены
- [ ] Бэкап БД в cron (`DEPLOY.md` §6)
- [ ] `ufw` открыт только 22/80/443; SSH по ключу

## Продукт

- [ ] Описание и about у @BotFather заполнены (`docs/LAUNCH_MATERIALS.md` §1)
- [ ] Аватар бота загружен
- [ ] Тестовый платеж Stars прошёл: купили Pro, `/stats` показывает 500 лимит
- [ ] Тестовый возврат: `/refund <charge_id>` — план вернулся в Free
- [ ] База знаний загружена на тестовом Pro-аккаунте, бот отвечает по ней
- [ ] Цены тарифов соответствуют плану (`PRO_PRICE_STARS` и т.д.)

## День запуска (docs/LAUNCH_MATERIALS.md §4)

- [ ] Пост-анонс в вашем личном канале/чате
- [ ] 3-5 посевов в тематических каналах
- [ ] Мониторинг: `/adminstats` через час после публикации

**После каждого пункта — отметьте. Незачёркнутых пунктов в «Продукт» быть не должно
к моменту, когда увидят первые платные пользователи.**