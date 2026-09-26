#!/bin/bash
# Update Script for Crypto Mining Server
# Updates T-Rex miner to latest version
# Run as: sudo bash /opt/my-mining-server/scripts/update.sh

set -e

echo "=== Crypto Mining Server Update ==="

# Stop the miner
echo "[1/4] Stopping miner service..."
systemctl stop miner || true

# Backup current config
echo "[2/4] Backing up configuration..."
cp /etc/miner/config/.env /etc/miner/config/.env.backup.$(date +%Y%m%d-%H%M%S) 2>/dev/null || true

# Get latest T-Rex version
echo "[3/4] Fetching latest T-Rex version..."
LATEST_VERSION=$(curl -s https://api.github.com/repos/trexminer/trex/releases/latest | grep -oP '"tag_name": "\K[^"]+')
if [ -z "$LATEST_VERSION" ]; then
    echo "ERROR: Could not fetch latest T-Rex version."
    exit 1
fi
echo "Latest version: $LATEST_VERSION"

# Check if update is needed
CURRENT_VERSION=$(/opt/trex/trex --version 2>/dev/null | grep -oP 'v?\K[0-9.]+' | head -1 || echo "unknown")
echo "Current version: $CURRENT_VERSION"

if [ "$CURRENT_VERSION" = "${LATEST_VERSION#v}" ]; then
    echo "Already on latest version. No update needed."
    systemctl start miner
    exit 0
fi

# Download and install latest T-Rex
echo "[4/4] Downloading and installing T-Rex $LATEST_VERSION..."
cd /opt/trex
TREX_VERSION_NUM="${LATEST_VERSION#v}"
TREX_URL="https://github.com/trexminer/trex/releases/download/${LATEST_VERSION}/trex-${TREX_VERSION_NUM}-linux.tar.gz"
wget -q "$TREX_URL" -O trex-new.tar.gz
tar -xzf trex-new.tar.gz
rm trex-new.tar.gz

# Set permissions
chown -R miner:miner /opt/trex
chmod +x /opt/trex/trex

# Start the miner
echo ""
echo "=== Update Complete ==="
systemctl start miner

# Verify
echo "Verifying..."
sleep 3
if systemctl is-active --quiet miner; then
    echo "SUCCESS: Miner is running with T-Rex $LATEST_VERSION"
else
    echo "WARNING: Miner failed to start. Check logs: sudo journalctl -u miner -n 50"
fi