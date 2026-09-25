# Quick Start Guide

## What You Need
- A computer with NVIDIA GPU
- Ubuntu 24.04 (or Windows with WSL)
- Internet connection
- ~$0 electricity (or your local rate)

## Step 1: Create Wallet (5 min)
1. Go to https://ravencoin.com/
2. Click "Get a Wallet"
3. Choose "Core Wallet" for Windows/Linux
4. Download and install it
5. Open it, create a new wallet
6. **WRITE DOWN the 12-word seed phrase on paper** — do not type it anywhere
7. Wait for the wallet to sync (this may take hours)

## Step 2: Get Your Address
1. Open Ravencoin Core
2. Click "Receive" at the top
3. Copy the address that starts with "R"
4. Example: `RWaPdLz6X5kVqN3vBnM8fGjKtQ2wErYcZx`

## Step 3: Set Up Mining Pool Account (2 min)
1. Go to https://2miners.com
2. Click "Sign up"
3. Create account with email
4. Go to "Ravencoin" section
5. Paste your RVN address
6. Set worker name (e.g., "my-gpu")

## Step 4: Run Setup (5 min)
```bash
# If you cloned this repo:
cd my-mining-server

# Edit .env with your wallet address
cp .env.example .env
nano .env  # Replace WALLET_ADDRESS with your RVN address

# Run setup (requires sudo)
sudo bash setup.sh
```

## Step 5: Start Mining
```bash
sudo systemctl start miner
```

## Step 6: Verify It's Working
```bash
# Check service status
sudo systemctl status miner

# Watch live logs
sudo journalctl -u miner -f

# Check GPU
nvidia-smi

# Check earnings at https://2miners.com/profile
```

## Step 7: Wait for Payouts
- The pool pays out automatically when you reach the minimum threshold
- Default threshold on 2miners is usually 50 RVN
- Check your wallet periodically
- RVN price fluctuates — check https://coinmarketcap.com/currencies/ravencoin/

## That's It!
Your GPU is now mining Ravencoin and earning you RVN. The service will restart automatically if it crashes, and it starts on boot.

## Need Help?
- README.md for full documentation
- EARN.md for detailed earning guide
- TROUBLESHOOTING.md for common problems