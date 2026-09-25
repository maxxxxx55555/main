# Project Manifest

## Files

| File | Purpose |
|------|---------|
| `README.md` | Full documentation with earning guide |
| `EARN.md` | Step-by-step earning instructions |
| `QUICK_START.md` | 5-minute quick start guide |
| `TROUBLESHOOTING.md` | Common problems and solutions |
| `SECURITY.md` | Security checklist |
| `MANIFEST.md` | This file - project inventory |
| `.env.example` | Environment template (copy to .env) |
| `.gitignore` | Files to exclude from git |
| `setup.sh` | One-command setup script |
| `scripts/apply_limits.sh` | GPU power/temp limits |
| `scripts/watchdog.sh` | Monitoring script |
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

# 3. Run setup
sudo bash setup.sh

# 4. Start miner
sudo systemctl start miner
```

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
sudo bash scripts/watchdog.sh  # Run watchdog check
nvidia-smi                     # GPU status
curl http://localhost:4068/api/v1/status  # Miner API
```

## Cron Setup
```bash
# Install watchdog cron (runs every 5 minutes)
sudo crontab -e
# Add this line:
*/5 * * * * /bin/bash /opt/my-mining-server/scripts/watchdog.sh >> /var/log/miner/watchdog-cron.log 2>&1
```

## Firewall Setup
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 4444
sudo ufw allow 4068
sudo ufw default deny incoming
```