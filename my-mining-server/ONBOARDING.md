# How Hard Is This? Realistic Difficulty Assessment

## Honest Answer: It's Easier Than You Think

If you can follow step-by-step instructions and have basic computer skills, you can do this in **1-2 hours total**. The setup.sh script does 90% of the work. You only need to:

1. Edit one file (nano .env)
2. Run one command (sudo bash setup.sh)
3. Run one more command (sudo systemctl start miner)

## Time Breakdown

| Task | Time Needed | Difficulty |
|------|-------------|------------|
| Clone repo | 2 minutes | EASY |
| Edit .env file | 3 minutes | EASY |
| Run setup.sh | 10-30 minutes | EASY (just wait) |
| Start miner | 1 second | EASY |
| Wait for rewards | Days/weeks | PASSIVE |
| **Total active time** | **~15 minutes** | |
| **Total wait time** | **~10-30 minutes** | |

## What setup.sh Does Automatically

You don't need to know any of this — it's all automated:

1. Installs NVIDIA driver (if not present)
2. Creates a secure `miner` user (not root)
3. Downloads T-Rex miner from GitHub
4. Configures systemd service (autostart on boot)
5. Sets GPU power limits (prevents overheating)
6. Configures firewall (only necessary ports open)
7. Installs watchdog cron (auto-restart if crash)
8. Copies all scripts to correct locations
9. Enables service for boot

## What You Need to Do Manually

### 1. Have a Wallet Address (5 min)
Go to https://ravencoin.com/ → Download Core Wallet → Create wallet → Write down 12-word seed phrase on paper → Copy your "R..." address.

**This is the hardest part conceptually:** You must keep your seed phrase safe. Anyone with it can steal your funds. Write it on paper, not in a file.

### 2. Edit .env File (3 min)
```bash
cp .env.example .env
nano .env
```
Change line 2 from:
```
WALLET_ADDRESS=your_rvn_wallet_address_here
```
To:
```
WALLET_ADDRESS=RWaPdLz6X5kVqN3vBnM8fGjKtQ2wErYcZx
```
Save (Ctrl+O, Enter, Ctrl+X).

### 3. Run Setup (10-30 min)
```bash
sudo bash setup.sh
```
Just watch it run. It downloads packages, installs driver, downloads T-Rex. Takes 10-30 minutes depending on your internet speed.

### 4. Start Miner (1 sec)
```bash
sudo systemctl start miner
```

### 5. Verify (1 min)
```bash
sudo systemctl status miner
```
Should show "active (running)".

## What Can Go Wrong

| Problem | Fix |
|---------|-----|
| "Permission denied" | You forgot `sudo` |
| "nvidia-smi not found" | Driver not installed. setup.sh installs it. Wait for reboot prompt. |
| "WALLET_ADDRESS not set" | Edit .env with your real RVN address |
| "Cannot connect to pool" | Check internet: `ping rvn.2miners.com` |
| Miner not starting | Run `sudo journalctl -u miner -n 50` to see error |
| Low hashrate | Check GPU temp: `nvidia-smi` |

## Prerequisites Check

Before starting, verify you have:

- [ ] Computer with NVIDIA GPU (GTX 1060 or better recommended)
- [ ] Ubuntu 24.04 installed (or Windows with WSL)
- [ ] Internet connection
- [ ] Admin/root access (for sudo commands)
- [ ] ~10 GB free disk space
- [ ] Patience (first run takes 10-30 min)

## If You Get Stuck

1. Read TROUBLESHOOTING.md
2. Check service logs: `sudo journalctl -u miner -n 100`
3. Check GPU: `nvidia-smi`
4. Check pool: https://2miners.com
5. Search T-Rex issues: https://github.com/trexminer/trex/issues

## Realistic Expectations

**You will NOT get rich quick.** Mining is a slow, steady process. With an RTX 3060, you might earn $0.10-$0.20 per day. With an RTX 4090, maybe $0.50 per day. Electricity costs may eat most of this.

**Mining is for:**
- Using idle GPU capacity
- Learning about crypto
- Long-term RVN accumulation
- Testing the setup

**Mining is NOT for:**
- Getting rich quick
- Replacing your income
- Beating electricity costs (check your local rates)

## Bottom Line

**Difficulty: 2/10** — much easier than most people think. The setup.sh script handles everything. You just need to edit one file and run two commands. The hardest part is keeping your seed phrase safe.

If you can install a game on your computer, you can do this.

## Need Help?

- QUICK_START.md — 5 minute guide
- TROUBLESHOOTING.md — fix common problems
- WITHDRAW.md — how to get money to your Russian card
- EARN.md — how much you can earn