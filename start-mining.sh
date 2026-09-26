#!/bin/bash
set -e
echo "=== Starting Mining Setup ==="
cd /tmp
rm -rf my-mining-server
git clone https://github.com/maxxxxx55555/main.git
cd main/my-mining-server
cp .env.example .env
echo ""
echo "!!! IMPORTANT: Edit .env now with your RVN wallet address !!!"
echo "Run: nano .env"
echo "Then replace WALLET_ADDRESS with your address starting with R..."
echo ""
read -p "Press Enter after editing .env to continue..."
sudo bash setup.sh
sudo systemctl start miner
echo ""
echo "=== DONE ==="
echo "Check status: sudo systemctl status miner"
echo "Check logs: sudo journalctl -u miner -f"
echo "Check GPU: nvidia-smi"
echo "Check earnings: https://2miners.com/profile"