#!/bin/bash
set -e
echo "========================================="
echo "  ONE-COMMAND LAUNCH: Mining + Bot"
echo "========================================="
echo ""

# === MINING SETUP ===
echo "[1/5] Cloning mining repository..."
cd /tmp
rm -rf my-mining-server
git clone https://github.com/maxxxxx55555/main.git
cd main/my-mining-server

echo ""
echo "[2/5] Creating .env file..."
cp .env.example .env

echo ""
echo "!!! IMPORTANT: Edit .env with your RVN wallet address !!!"
echo "Command: nano .env"
echo "Replace WALLET_ADDRESS with your address starting with R..."
echo ""
read -p "Press Enter after editing .env to continue..."

echo ""
echo "[3/5] Running setup.sh (10-30 minutes)..."
sudo bash setup.sh

echo ""
echo "[4/5] Starting miner..."
sudo systemctl start miner

echo ""
echo "[5/5] Starting bot..."
cd /tmp
rm -rf aibot
git clone https://github.com/maxxxxx55555/aibot.git
cd aibot
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "!!! IMPORTANT: Edit .env with your bot token !!!"
    echo "Command: nano .env"
    echo ""
    read -p "Press Enter after editing .env to continue..."
fi
if [ -f docker-compose.yml ]; then
    sudo docker compose up -d --build
else
    sudo bash deploy.sh
fi

echo ""
echo "========================================="
echo "  ALL DONE"
echo "========================================="
echo ""
echo "Mining:"
echo "  Status: sudo systemctl status miner"
echo "  Logs:   sudo journalctl -u miner -f"
echo "  GPU:    nvidia-smi"
echo "  Earnings: https://2miners.com/profile"
echo ""
echo "Bot:"
echo "  Status: sudo systemctl status bot"
echo "  Logs:   sudo journalctl -u bot -f"