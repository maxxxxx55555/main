#!/bin/bash
# Crypto Mining Server Setup Script
# Safe defaults: Ubuntu 24.04, NVIDIA GPU, Ravencoin/KawPow, T-Rex miner
# Run as: sudo bash setup.sh
# Usage: Run from the directory containing this script (my-mining-server/)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Crypto Mining Server Setup ==="
echo "Working directory: $SCRIPT_DIR"

# 1. Update system
echo "[1/8] Updating system packages..."
apt-get update -y
apt-get upgrade -y

# 2. Install NVIDIA driver (if not already installed)
echo "[2/8] Installing NVIDIA driver..."
if ! command -v nvidia-smi &> /dev/null; then
    apt-get install -y nvidia-driver-525 nvidia-utils-525
    echo "NVIDIA driver installed. A reboot may be required."
else
    echo "NVIDIA driver already installed."
fi

# 3. Create dedicated miner user (no root for miner)
echo "[3/8] Creating miner user..."
if ! id "miner" &>/dev/null; then
    useradd -m -s /bin/bash miner
    usermod -aG video miner
    usermod -aG input miner
    echo "Miner user created."
else
    echo "Miner user already exists."
fi

# 4. Install T-Rex miner
echo "[4/8] Installing T-Rex miner..."
MINER_DIR=/opt/trex
mkdir -p "$MINER_DIR"
cd "$MINER_DIR"

# Get latest T-Rex release for Linux
LATEST_VERSION=$(curl -s https://api.github.com/repos/trexminer/trex/releases/latest | grep -oP '"tag_name": "\K[^"]+')
echo "Latest T-Rex version: $LATEST_VERSION"

# T-Rex releases use format: trex-{version}-linux.tar.gz (version without 'v' prefix)
# Strip 'v' prefix if present
TREX_VERSION_NUM="${LATEST_VERSION#v}"
TREX_URL="https://github.com/trexminer/trex/releases/download/${LATEST_VERSION}/trex-${TREX_VERSION_NUM}-linux.tar.gz"
echo "Downloading from: $TREX_URL"
wget -q "$TREX_URL" -O trex.tar.gz
tar -xzf trex.tar.gz
rm trex.tar.gz

# Set permissions
chown -R miner:miner "$MINER_DIR"
chmod +x "$MINER_DIR/trex"

echo "T-Rex installed at $MINER_DIR/trex"

# 5. Create directories
echo "[5/8] Creating configuration directories..."
mkdir -p /etc/miner/config
mkdir -p /var/log/miner
mkdir -p /opt/my-mining-server/scripts
mkdir -p /opt/my-mining-server/deploy
chown -R miner:miner /etc/miner/config
chown -R miner:miner /var/log/miner
chown -R miner:miner /opt/my-mining-server

# Copy scripts to /opt/my-mining-server for watchdog access
cp "$SCRIPT_DIR/scripts/apply_limits.sh" /opt/my-mining-server/scripts/
cp "$SCRIPT_DIR/scripts/watchdog.sh" /opt/my-mining-server/scripts/
cp "$SCRIPT_DIR/deploy/miner.service" /opt/my-mining-server/deploy/
chmod +x /opt/my-mining-server/scripts/*.sh
chown -R miner:miner /opt/my-mining-server

# 6. Copy environment file
echo "[6/8] Setting up environment..."
if [ ! -f /etc/miner/config/.env ]; then
    cp "$SCRIPT_DIR/.env.example" /etc/miner/config/.env
    chmod 600 /etc/miner/config/.env
    chown miner:miner /etc/miner/config/.env
    echo "Please edit /etc/miner/config/.env with your wallet address."
else
    echo "Environment file already exists."
fi

# 7. Install systemd service
echo "[7/8] Installing systemd service..."
cp "$SCRIPT_DIR/deploy/miner.service" /etc/systemd/system/miner.service
systemctl daemon-reload
systemctl enable miner.service
echo "Miner service enabled (will start on boot)."

# 8. Apply GPU limits (if NVIDIA GPU detected)
echo "[8/8] Applying GPU power/temp limits..."
if command -v nvidia-smi &> /dev/null; then
    bash "$SCRIPT_DIR/scripts/apply_limits.sh"
else
    echo "NVIDIA GPU not detected, skipping GPU limits."
fi

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Edit /etc/miner/config/.env with your wallet address"
echo "2. Run: sudo systemctl start miner"
echo "3. Check status: sudo systemctl status miner"
echo "4. View logs: sudo journalctl -u miner -f"