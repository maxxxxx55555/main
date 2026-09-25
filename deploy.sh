#!/usr/bin/env bash
# Деплой AI-Сотрудника на Ubuntu VPS (Hetzner / DigitalOcean / любой с apt).
# Использование: bash deploy.sh
set -euo pipefail

echo "=== 1/6 Проверка прав и обновление системы ==="
if [ "$EUID" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi
$SUDO apt-get update -y && $SUDO apt-get upgrade -y

echo "=== 2/6 Установка Docker + compose-плагин ==="
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  $SUDO systemctl enable --now docker
fi
docker compose version || { echo "docker compose plugin не найден"; exit 1; }

echo "=== 3/6 Код проекта ==="
if [ ! -d ai-employee ]; then
  git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> ai-employee
fi
cd ai-employee
git pull --ff-only || true

echo "=== 4/6 Конфигурация .env ==="
if [ ! -f .env ]; then
  cp .env.example .env
  echo ">>> Заполните .env: BOT_TOKEN (обязательно), LLM_API_KEY, ADMIN_IDS"
  echo ">>> Откройте: nano .env"
  nano .env
fi

echo "=== 5/6 Сборка и старт (prod-профиль: PostgreSQL + Redis) ==="
docker compose --profile prod up -d --build

echo "=== 6/6 Статус (миграции применяются приложением автоматически) ==="
docker compose --profile prod exec -T app alembic current
docker compose --profile prod ps
curl -fsS http://localhost:8080/health && echo " <- /health OK"

echo ""
echo "✅ Готово. Логи: docker compose logs -f app"
echo "   Остановка: docker compose --profile prod down"