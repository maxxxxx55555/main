#!/bin/bash
set -e
echo "=== Starting Bot Setup ==="
cd /tmp
rm -rf aibot
git clone https://github.com/maxxxxx55555/aibot.git
cd aibot
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "!!! IMPORTANT: Edit .env now with your bot token and config !!!"
    echo "Run: nano .env"
    echo ""
    read -p "Press Enter after editing .env to continue..."
fi
if [ -f docker-compose.yml ]; then
    sudo docker compose up -d --build
else
    sudo bash deploy.sh
fi
echo ""
echo "=== DONE ==="
echo "Check status: sudo systemctl status bot"
echo "Check logs: sudo journalctl -u bot -f"