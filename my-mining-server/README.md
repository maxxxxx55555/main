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
sudo bash /opt/my-mining-server/scripts/watchdog.sh
```

### GPU Limits
```bash
# Apply power/temp limits
sudo bash /opt/my-mining-server/scripts/apply_limits.sh

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

Firewall and watchdog cron are automatically configured by setup.sh.
To manually verify:
```bash
sudo ufw status              # Check firewall rules
sudo crontab -l              # Check watchdog cron entry
```

- Miner runs as non-root `miner` user
- Secrets stored in `/etc/miner/config/.env` with `chmod 600`
- Firewall enabled (only SSH + miner ports)
- No hardcoded credentials in code
- T-Rex binary from official GitHub releases
- Full security checklist: see SECURITY.md

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

## How to Earn (Step by Step)

### 1. Create a Ravencoin Wallet
Go to https://ravencoin.com/ → click "Get a Wallet" → choose "Core Wallet" for desktop. Follow the setup wizard. When asked, create a new wallet and **write down your 12-word seed phrase on paper**. Never share it. This seed phrase is your master key — anyone with it can steal your funds.

### 2. Get Your Address
Open your Ravencoin Core wallet. Click "Receive" at the top. You will see a long address starting with "R". Copy it. This is your WALLET_ADDRESS. Example: `RWaPdLz6X5kVqN3vBnM8fGjKtQ2wErYcZx`

### 3. Register on a Mining Pool
Go to https://2miners.com. Click "Sign up" (or just use without account for solo mining). Create an account if you want detailed stats. Then navigate to the Ravencoin section. Add your wallet address there. The pool will assign you a worker name — or you can set it yourself.

### 4. Configure the Miner
Edit the file `/etc/miner/config/.env` after running setup.sh:
- Replace `WALLET_ADDRESS=your_rvn_wallet_address_here` with your actual RVN address
- Leave `POOL_PASSWORD=x` (most pools accept 'x' as default)
- Adjust `POWER_LIMIT=85` if you want less power draw
- Adjust `TEMP_TARGET=70` if your GPU runs hotter

### 5. Start Mining
Run `sudo systemctl start miner`. Your GPU will now solve cryptographic puzzles and earn RVN rewards. The pool pays out automatically based on your contributed hashrate. Payouts go to your wallet address.

### 6. Check Your Earnings
- Open your Ravencoin Core wallet to see incoming RVN
- Visit the 2miners dashboard: https://2miners.com/profile (if you created an account)
- Check the T-Rex API at http://your-server-ip:4068 for live hashrate

### Estimated Earnings (Approximate)
These are rough estimates and fluctuate with RVN price and network difficulty:

| GPU | Approx. Daily RVN | Approx. Daily USD (at $0.05/RVN) |
|-----|-------------------|----------------------------------|
| RTX 3060 | 1.5-2.5 RVN | $0.08-0.13 |
| RTX 3070 | 2.5-4 RVN | $0.13-0.20 |
| RTX 3080 | 4-6 RVN | $0.20-0.30 |
| RTX 4090 | 7-10 RVN | $0.35-0.50 |

**Warning:** Electricity costs may exceed earnings on cheap GPU models. Calculate your local electricity cost per kWh against these numbers before running 24/7.

### 7. Withdraw to Exchange (Optional)
Once you have enough RVN in your wallet, you can:
- Send it to an exchange like Binance, KuCoin, or Kraken
- Sell it for USD, USDT, or other cryptocurrencies
- Or hold it as an investment

### Important Notes
- RVN price is volatile — you may earn more or less than estimated
- Mining difficulty adjusts based on total network hashrate
- Pool fees are typically 1-2%
- T-Rex miner fee is 1% of your earnings
- Always keep your seed phrase safe and offline
- Check https://ravencoin.com/ for official updates

## License
MIT