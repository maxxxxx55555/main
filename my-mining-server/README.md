# Crypto Mining Server

Secure, legal, and stable GPU mining setup for Ravencoin (RVN) using T-Rex miner on Ubuntu.

## Quick Start

### Prerequisites
- Ubuntu 24.04 (or 22.04)
- NVIDIA GPU with driver installed
- Admin/root access for setup

### Installation

1. **Clone/Download this repository**
   ```bash
   git clone https://github.com/maxxxxx55555/main.git
   cd main/my-mining-server
   ```

2. **Edit environment file**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your wallet address and settings
   ```

3. **Run setup script** (requires sudo)
   ```bash
   sudo bash setup.sh
   ```

4. **Edit the installed config** (after setup)
   ```bash
   sudo nano /etc/miner/config/.env
   ```

5. **Start the miner**
   ```bash
   sudo systemctl start miner
   ```

## Management Commands

### Service Control
```bash
# Start miner
sudo systemctl start miner

# Stop miner
sudo systemctl stop miner

# Restart miner
sudo systemctl restart miner

# Check status
sudo systemctl status miner

# Enable autostart on boot
sudo systemctl enable miner

# Disable autostart
sudo systemctl disable miner
```

### Monitoring
```bash
# View live logs
sudo journalctl -u miner -f

# View last 100 lines
sudo journalctl -u miner -n 100

# Check miner API (if enabled)
curl http://localhost:4068/api/v1/status

# Check GPU status
nvidia-smi

# Run watchdog check
sudo bash scripts/watchdog.sh
```

### GPU Limits
```bash
# Apply power/temp limits
sudo bash scripts/apply_limits.sh

# Check current limits
nvidia-smi --query-gpu=power.default_limit,temperature.gpu --format=csv
```

## Configuration

All settings are in `/etc/miner/config/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `WALLET_ADDRESS` | *required* | Your RVN wallet address |
| `POOL_URL` | `rvn.2miners.com:4444` | Pool URL |
| `WORKER_NAME` | `worker1` | Worker name for multi-GPU |
| `API_PORT` | `4068` | T-Rex API port |
| `POWER_LIMIT` | `85` | GPU power limit (%) |
| `TEMP_TARGET` | `70` | Temperature target (°C) |
| `EXTRA_FLAGS` | *(empty)* | Additional T-Rex flags |
| `POOL_PASSWORD` | `x` | Pool password |

## Troubleshooting

### Miner won't start
```bash
# Check service status
sudo systemctl status miner

# Check config file
sudo cat /etc/miner/config/.env

# Check permissions
sudo ls -la /etc/miner/config/
```

### Low hashrate
- Check GPU temperature: `nvidia-smi`
- Check power limits: `nvidia-smi --query-gpu=power.draw,power.limit`
- Check for thermal throttling

### Can't connect to pool
- Check internet: `ping rvn.2miners.com`
- Check firewall: `sudo ufw status`
- Verify pool URL in config

## Security

- Miner runs as non-root `miner` user
- Secrets stored in `/etc/miner/config/.env` with `chmod 600`
- Firewall enabled (only SSH + miner ports)
- No hardcoded credentials in code
- T-Rex binary from official GitHub releases

## Backup

```bash
# Backup config
sudo cp /etc/miner/config/.env /backup/miner-config-$(date +%Y%m%d).env

# Backup logs
sudo cp -r /var/log/miner /backup/miner-logs-$(date +%Y%m%d)
```

## Update

```bash
# Stop miner
sudo systemctl stop miner

# Download latest T-Rex
cd /opt/trex
wget -q https://github.com/trexminer/trex/releases/latest/download/trex-linux.tar.gz
tar -xzf trex-linux.tar.gz
rm trex-linux.tar.gz

# Start miner
sudo systemctl start miner
```

## License
MIT