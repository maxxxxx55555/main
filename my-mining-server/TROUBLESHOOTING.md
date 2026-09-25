# Troubleshooting Guide

## Problem: Miner won't start
**Symptoms:** `sudo systemctl status miner` shows "failed" or "inactive"

**Solutions:**
1. Check the config file:
   ```bash
   sudo cat /etc/miner/config/.env
   ```
   Make sure WALLET_ADDRESS is filled in.

2. Check if T-Rex binary exists:
   ```bash
   ls -la /opt/trex/trex
   ```

3. Check service logs:
   ```bash
   sudo journalctl -u miner -n 50
   ```

4. Try starting manually to see the error:
   ```bash
   sudo -u miner /opt/trex/trex -a kawpow -u YOUR_WALLET -p x -w worker1 --api-port 4068 rvn.2miners.com:4444
   ```

## Problem: No hashrate or low hashrate
**Symptoms:** T-Rex shows 0 H/s or much lower than expected

**Solutions:**
1. Check GPU temperature:
   ```bash
   nvidia-smi
   ```
   If temp > 80°C, the GPU may be thermal throttling.

2. Check power limit:
   ```bash
   nvidia-smi --query-gpu=power.draw,power.limit --format=csv
   ```
   If power.draw is much lower than power.limit, reduce the limit.

3. Check for driver issues:
   ```bash
   nvidia-smi
   ```
   Make sure the driver is loaded and GPU is visible.

4. Update T-Rex to latest version:
   ```bash
   sudo systemctl stop miner
   cd /opt/trex
   wget -q https://github.com/trexminer/trex/releases/latest/download/trex-linux.tar.gz
   tar -xzf trex-linux.tar.gz
   sudo systemctl start miner
   ```

## Problem: Can't connect to pool
**Symptoms:** T-Rex shows "Connection refused" or "Pool unreachable"

**Solutions:**
1. Test internet connection:
   ```bash
   ping rvn.2miners.com
   ```

2. Check if port 4444 is blocked:
   ```bash
   telnet rvn.2miners.com 4444
   ```

3. Check firewall:
   ```bash
   sudo ufw status
   ```
   If active, allow the port:
   ```bash
   sudo ufw allow 4444
   ```

4. Try a different pool:
   Edit `/etc/miner/config/.env` and change POOL_URL to:
   ```
   POOL_URL=rvn.pool.nicehash.com:4444
   ```
   or
   ```
   POOL_URL=rvn.zpool.ca:4444
   ```

## Problem: Miner crashes repeatedly
**Symptoms:** Service keeps restarting in a loop

**Solutions:**
1. Check the restart count:
   ```bash
   sudo systemctl status miner
   ```
   Look for "StartLimitInterval" and "StartLimitBurst"

2. Reset the service state:
   ```bash
   sudo systemctl reset-failed miner
   ```

3. Check for GPU issues:
   ```bash
   nvidia-smi
   ```
   Make sure GPU is not overheating or failing.

4. Reduce power limit:
   Edit `/etc/miner/config/.env` and set:
   ```
   POWER_LIMIT=70
   ```

## Problem: Wallet not receiving payments
**Symptoms:** Pool shows earnings but wallet balance is 0

**Solutions:**
1. Verify your wallet address is correct:
   ```bash
   sudo cat /etc/miner/config/.env
   ```
   Make sure WALLET_ADDRESS matches your Ravencoin Core "Receive" address.

2. Check pool dashboard:
   Visit https://2miners.com/profile and check your worker stats.

3. Check wallet sync status:
   Open Ravencoin Core and check if the blockchain is synced.

4. Wait for payout threshold:
   Most pools require a minimum balance before paying out (e.g., 50 RVN).

## Problem: Windows instead of Ubuntu
**Solutions:**
Use Windows Subsystem for Linux (WSL):
```powershell
# Enable WSL
wsl --install

# Install Ubuntu from Microsoft Store
# Then follow the Ubuntu instructions above
```

## Problem: AMD GPU instead of NVIDIA
**Solutions:**
T-Rex is NVIDIA-only. For AMD GPUs:
1. Use GMiner instead: https://github.com/gminerminer/gminer
2. Download and replace T-Rex with GMiner
3. Update the service file to use GMiner instead of T-Rex

## Getting Help
If none of the above works:
1. Check service logs: `sudo journalctl -u miner -n 100`
2. Check GPU status: `nvidia-smi`
3. Check pool dashboard: https://2miners.com/profile
4. Search T-Rex issues: https://github.com/trexminer/trex/issues