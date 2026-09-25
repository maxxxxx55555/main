# How to Earn with This Mining Setup

## Step 1: Create a Wallet
Go to https://ravencoin.com/ and click "Get a Wallet". Choose "Core Wallet" for desktop. Follow the setup wizard. When asked, create a new wallet and **write down your 12-word seed phrase on paper**. Never share it. This seed phrase is your master key — anyone with it can steal your funds.

## Step 2: Get Your Address
Open your Ravencoin Core wallet. Click "Receive" at the top. You will see a long address starting with "R". Copy it. This is your WALLET_ADDRESS. Example: `RWaPdLz6X5kVqN3vBnM8fGjKtQ2wErYcZx`

## Step 3: Register on a Mining Pool
Go to https://2miners.com. Click "Sign up" (or just use without account for solo mining). Create an account if you want detailed stats. Then navigate to the Ravencoin section. Add your wallet address there. The pool will assign you a worker name — or you can set it yourself.

## Step 4: Configure the Miner
Edit the file `/etc/miner/config/.env` after running setup.sh:
- Replace `WALLET_ADDRESS=your_rvn_wallet_address_here` with your actual RVN address
- Leave `POOL_PASSWORD=x` (most pools accept 'x' as default)
- Adjust `POWER_LIMIT=85` if you want less power draw
- Adjust `TEMP_TARGET=70` if your GPU runs hotter

## Step 5: Start Mining
Run `sudo systemctl start miner`. Your GPU will now solve cryptographic puzzles and earn RVN rewards. The pool pays out automatically based on your contributed hashrate. Payouts go to your wallet address.

## Step 6: Check Your Earnings
- Open your Ravencoin Core wallet to see incoming RVN
- Visit the 2miners dashboard: https://2miners.com/profile (if you created an account)
- Check the T-Rex API at http://your-server-ip:4068 for live hashrate

## Estimated Earnings (Approximate)
These are rough estimates and fluctuate with RVN price and network difficulty:

| GPU | Approx. Daily RVN | Approx. Daily USD (at $0.05/RVN) |
|-----|-------------------|----------------------------------|
| RTX 3060 | 1.5-2.5 RVN | $0.08-0.13 |
| RTX 3070 | 2.5-4 RVN | $0.13-0.20 |
| RTX 3080 | 4-6 RVN | $0.20-0.30 |
| RTX 4090 | 7-10 RVN | $0.35-0.50 |

**Warning:** Electricity costs may exceed earnings on cheap GPU models. Calculate your local electricity cost per kWh against these numbers before running 24/7.

## Step 7: Withdraw to Exchange (Optional)
Once you have enough RVN in your wallet, you can:
- Send it to an exchange like Binance, KuCoin, or Kraken
- Sell it for USD, USDT, or other cryptocurrencies
- Or hold it as an investment

## Important Notes
- RVN price is volatile — you may earn more or less than estimated
- Mining difficulty adjusts based on total network hashrate
- Pool fees are typically 1-2%
- T-Rex miner fee is 1% of your earnings
- Always keep your seed phrase safe and offline
- Check https://ravencoin.com/ for official updates