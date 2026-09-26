# Update Guide

## When to Update

- New T-Rex version released with bug fixes or performance improvements
- After major system updates (Ubuntu kernel, NVIDIA driver)
- If you experience crashes or low hashrate

## Check for Updates

```bash
# Check current T-Rex version
/opt/trex/trex --version

# Check latest available version
curl -s https://api.github.com/repos/trexminer/trex/releases/latest | grep -oP '"tag_name": "\K[^"]+'
```

## Update T-Rex Miner

### Method 1: Re-run setup.sh (Recommended)
```bash
sudo bash setup.sh
```
This will download the latest T-Rex version automatically.

### Method 2: Manual Update
```bash
# Stop the miner
sudo systemctl stop miner

# Download latest T-Rex
cd /opt/trex
wget -q https://github.com/trexminer/trex/releases/latest/download/trex-linux.tar.gz
tar -xzf trex-linux.tar.gz
rm trex-linux.tar.gz

# Verify the binary exists and is executable
ls -la /opt/trex/trex

# Start the miner
sudo systemctl start miner
```

### Method 3: Update via Script
```bash
sudo bash /opt/my-mining-server/scripts/update.sh
```

## Update NVIDIA Driver

```bash
# Check current driver version
nvidia-smi | grep "Driver Version"

# Update driver
sudo apt-get update
sudo apt-get install --reinstall nvidia-driver-525

# Reboot if required
sudo reboot
```

## Update Ubuntu System

```bash
# Update package lists
sudo apt-get update

# Upgrade packages
sudo apt-get upgrade -y

# Optional: full upgrade (may remove unused packages)
sudo apt-get dist-upgrade -y

# Reboot if kernel was updated
sudo reboot
```

## After Update Verification

After any update, verify everything works:

```bash
# Check service status
sudo systemctl status miner

# Check GPU
nvidia-smi

# Check logs for errors
sudo journalctl -u miner -n 50

# Check hashrate via API
curl http://localhost:4068/api/v1/status

# Check pool dashboard
# Visit https://2miners.com/profile
```

## Rollback Procedure

If an update causes problems:

### Rollback T-Rex
```bash
# Stop miner
sudo systemctl stop miner

# Download previous version (replace VERSION with the old version)
cd /opt/trex
wget -q https://github.com/trexminer/trex/releases/download/VERSION/trex-VERSION-linux.tar.gz
tar -xzf trex-VERSION-linux.tar.gz
rm trex-VERSION-linux.tar.gz

# Start miner
sudo systemctl start miner
```

### Rollback NVIDIA Driver
```bash
# Install previous driver version
sudo apt-get install --reinstall nvidia-driver-525=VERSION

# Reboot
sudo reboot
```

## Backup Before Update

Always backup config before updating:
```bash
sudo cp /etc/miner/config/.env /backup/miner-config-$(date +%Y%m%d).env
```

## Update Schedule

- **T-Rex:** Check monthly for new releases
- **NVIDIA Driver:** Check quarterly for new versions
- **Ubuntu:** Check monthly for security updates
- **Full system update:** Every 3-6 months