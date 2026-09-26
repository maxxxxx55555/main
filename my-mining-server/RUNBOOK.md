# Runbook: Recovery and Maintenance

## If Miner Stops Working

### Step 1: Check Service Status
```bash
sudo systemctl status miner
```
Look for:
- "active (running)" — everything is fine
- "inactive (dead)" — miner is stopped
- "failed" — miner crashed
- "activating" — starting up

### Step 2: Check Logs
```bash
# Last 50 lines of logs
sudo journalctl -u miner -n 50

# Live log tail
sudo journalctl -u miner -f
```

Common errors:
- "WALLET_ADDRESS not set" — edit /etc/miner/config/.env
- "Cannot connect to pool" — check internet
- "CUDA error" or "out of memory" — reduce power limit

### Step 3: Restart the Miner
```bash
sudo systemctl restart miner
```

### Step 4: If Still Not Working
```bash
# Reset failed state
sudo systemctl reset-failed miner

# Try starting manually to see the error
sudo -u miner /opt/trex/trex -a kawpow -u YOUR_WALLET -p x -w worker1 --api-port 4068 rvn.2miners.com:4444
```

## If GPU Overheats

### Check Temperature
```bash
nvidia-smi
```
Look for:
- Temperature column — should be under 80°C
- Power draw — should match your power limit
- Fan speed — should be non-zero

### If Temperature > 85°C:
1. Reduce power limit:
```bash
sudo nano /etc/miner/config/.env
# Change POWER_LIMIT=85 to POWER_LIMIT=70
```
2. Restart miner:
```bash
sudo systemctl restart miner
```

3. Check cooling:
- Is the GPU fan working?
- Is there dust on the heatsink?
- Is the case well-ventilated?

## If Hashrate Drops to Zero

### Check Pool Connection
```bash
# Test internet
ping rvn.2miners.com

# Check if port is open
telnet rvn.2miners.com 4444
```

### Check GPU
```bash
nvidia-smi
```
Make sure GPU is visible and not throttling.

### Check Miner API
```bash
curl http://localhost:4068/api/v1/status
```
If this returns an error, the miner may have crashed.

## If Watchdog Fails

### Check Cron
```bash
sudo crontab -l
```
Make sure the cron line is present:
```
*/5 * * * * /bin/bash /opt/my-mining-server/scripts/watchdog.sh >> /var/log/miner/watchdog-cron.log 2>&1
```

### Run Watchdog Manually
```bash
sudo bash /opt/my-mining-server/scripts/watchdog.sh
```

### Check Watchdog Logs
```bash
cat /var/log/miner/watchdog.log
cat /var/log/miner/watchdog-cron.log
```

## After System Reboot

The miner should start automatically (systemd enabled). Verify:
```bash
sudo systemctl status miner
```
If not running:
```bash
sudo systemctl start miner
```

## Full Recovery Procedure

If nothing works, do a full reset:

### 1. Stop the miner
```bash
sudo systemctl stop miner
```

### 2. Reset systemd state
```bash
sudo systemctl reset-failed miner
```

### 3. Verify config
```bash
sudo cat /etc/miner/config/.env
```
Make sure WALLET_ADDRESS is set.

### 4. Verify T-Rex binary
```bash
ls -la /opt/trex/trex
```
If missing, re-run setup.sh:
```bash
sudo bash setup.sh
```

### 5. Start miner
```bash
sudo systemctl start miner
```

### 6. Verify
```bash
sudo systemctl status miner
sudo journalctl -u miner -n 20
nvidia-smi
```

## Emergency Stop

To immediately stop all mining:
```bash
sudo systemctl stop miner
```

To kill the miner process directly:
```bash
sudo pkill -f trex
```

To disable autostart:
```bash
sudo systemctl disable miner
```

## Contact Support

If none of the above works:
1. Check service logs: `sudo journalctl -u miner -n 100`
2. Check GPU status: `nvidia-smi`
3. Check pool dashboard: https://2miners.com/profile
4. Search T-Rex issues: https://github.com/trexminer/trex/issues