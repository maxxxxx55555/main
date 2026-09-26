# Mining Server

One-command GPU mining setup for Ravencoin (RVN) on Ubuntu WSL.

## Quick Start (Windows)

### Option A: Mining Only

1. Download `START-MINING.ps1` from this repo
2. Double-click it
3. Enter your RVN wallet address when prompted
4. Enter your card last 4 digits (for reference only)
5. Wait 10-30 minutes for setup
6. Done — miner is running

### Option B: Mining + Telegram Bot

1. Download `START-ALL.ps1` from this repo
2. Double-click it
3. Enter your RVN wallet address
4. Enter your card last 4 digits
5. Enter your Telegram bot token (from @BotFather)
6. Enter your admin user ID (from @userinfobot)
7. Wait 10-30 minutes
8. Done — both are running

### Option C: Bash (Linux/Mac)

```bash
wget https://raw.githubusercontent.com/maxxxxx55555/main/start-all.sh
chmod +x start-all.sh
sudo bash start-all.sh
```

## What Gets Installed

- NVIDIA driver (if not present)
- T-Rex miner (latest version)
- systemd service (autostart on boot)
- GPU power/temp limits (prevents overheating)
- Firewall (only necessary ports)
- Watchdog cron (auto-restart on crash)

## Management Commands

```bash
# Check status
wsl -d Ubuntu bash -c 'sudo systemctl status miner'

# View logs
wsl -d Ubuntu bash -c 'sudo journalctl -u miner -f'

# Check GPU
wsl -d Ubuntu bash -c 'nvidia-smi'

# Stop miner
wsl -d Ubuntu bash -c 'sudo systemctl stop miner'

# Start miner
wsl -d Ubuntu bash -c 'sudo systemctl start miner'

# Restart miner
wsl -d Ubuntu bash -c 'sudo systemctl restart miner'
```

## Earnings

- Check pool: https://2miners.com/profile
- Check wallet: https://ravencoin.com/
- See WITHDRAW.md for how to withdraw to Russian card
- See WITHOUT_IP.md for mining without IP/self-employment

## Documentation

| File | Description |
|------|-------------|
| `README.md` | This file |
| `my-mining-server/README.md` | Full documentation |
| `my-mining-server/QUICK_START.md` | 5-minute quick start |
| `my-mining-server/EARN.md` | How to earn |
| `my-mining-server/WITHDRAW.md` | Withdraw to Russian card |
| `my-mining-server/WITHOUT_IP.md` | Without IP/self-employment |
| `my-mining-server/RUNBOOK.md` | Recovery procedures |
| `my-mining-server/UPDATE.md` | Update guide |
| `my-mining-server/SECURITY.md` | Security checklist |
| `my-mining-server/TROUBLESHOOTING.md` | Fix common problems |
| `my-mining-server/ONBOARDING.md` | Difficulty assessment |

## Project Structure

```
.
├── START-MINING.ps1    # Windows: mining only
├── START-BOT.ps1       # Windows: bot only
├── START-ALL.ps1       # Windows: mining + bot
├── start-mining.sh     # Linux: mining only
├── start-bot.sh        # Linux: bot only
├── start-all.sh        # Linux: mining + bot
└── my-mining-server/   # Mining project
    ├── setup.sh        # One-command setup
    ├── scripts/        # GPU limits, watchdog, update
    └── deploy/         # systemd service, cron
```

## Requirements

- Windows 10/11 with WSL
- NVIDIA GPU
- Internet connection
- ~10 GB free disk space