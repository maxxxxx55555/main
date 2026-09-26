# Project Manifest

## Files

| File | Purpose |
|------|---------|
| `README.md` | Full documentation with earning guide |
| `EARN.md` | Step-by-step earning instructions |
| `QUICK_START.md` | 5-minute quick start guide |
| `TROUBLESHOOTING.md` | Common problems and solutions |
| `SECURITY.md` | Security checklist |
| `RUNBOOK.md` | Recovery and maintenance procedures |
| `ONBOARDING.md` | Difficulty assessment and what to expect |
| `WITHDRAW.md` | How to withdraw to Russian bank card |
| `WITHOUT_IP.md` | Mining without IP/self-employment |
| `MANIFEST.md` | This file - project inventory |
| `.env.example` | Environment template (copy to .env) |
| `.gitignore` | Files to exclude from git |
| `setup.sh` | One-command setup script |
| `scripts/apply_limits.sh` | GPU power/temp limits |
| `scripts/watchdog.sh` | Monitoring script |
| `scripts/update.sh` | Update script for T-Rex miner |
| `deploy/miner.service` | systemd service unit |
| `deploy/watchdog.cron` | Cron configuration for watchdog |

## Directory Structure
```
my-mining-server/
├── .env.example
├── .gitignore
├── MANIFEST.md
├── README.md
├── EARN.md
├── QUICK_START.md
├── SECURITY.md
├── TROUBLESHOOTING.md
├── RUNBOOK.md
├── ONBOARDING.md
├── WITHDRAW.md
├── WITHOUT_IP.md
├── setup.sh
├── scripts/
│   ├── apply_limits.sh
│   └── watchdog.sh
└── deploy/
    ├── miner.service
    └── watchdog.cron
```

## Setup Commands
```bash
# 1. Clone repo
git clone https://github.com/maxxxxx55555/main.git
cd main/my-mining-server

# 2. Edit .env
cp .env.example .env
nano .env

# 3. Run setup (does everything: driver, T-Rex, systemd, firewall, cron, GPU limits)
sudo bash setup.sh

# 4. Start miner
sudo systemctl start miner
```

## What setup.sh Does (10 Steps)
1. Updates system packages
2. Installs NVIDIA driver if needed
3. Creates non-root `miner` user
4. Downloads and installs T-Rex miner
5. Creates config directories and copies scripts to /opt/my-mining-server
6. Copies .env.example to /etc/miner/config/.env
7. Installs and enables systemd service (autostart on boot)
8. Applies GPU power/temp limits
9. Configures firewall (SSH + ports 4444, 4068)
10. Installs watchdog cron (runs every 5 minutes)

## Management Commands
```bash
sudo systemctl start miner     # Start
sudo systemctl stop miner      # Stop
sudo systemctl restart miner   # Restart
sudo systemctl status miner    # Status
sudo systemctl enable miner    # Autostart on boot
sudo systemctl disable miner   # Disable autostart
sudo journalctl -u miner -f   # View logs
```

## Monitoring Commands
```bash
sudo bash /opt/my-mining-server/scripts/watchdog.sh  # Run watchdog check
nvidia-smi                     # GPU status
curl http://localhost:4068/api/v1/status  # Miner API
sudo ufw status                # Check firewall rules
sudo crontab -l                # Check watchdog cron entry
```