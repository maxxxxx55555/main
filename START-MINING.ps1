# ============================================
#  MINING LAUNCHER - WINDOWS
#  One script to rule them all
# ============================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  MINING SETUP - WINDOWS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: Check for WSL ---
Write-Host "[1/6] Checking for WSL..." -ForegroundColor Yellow
$wsl = wsl --status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "WSL not found. Installing WSL..." -ForegroundColor Red
    wsl --install --no-launch
    Write-Host "WSL installed. Please restart your computer, then run this script again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "WSL is available." -ForegroundColor Green
Write-Host ""

# --- Step 2: Check/Install Ubuntu ---
Write-Host "[2/6] Checking Ubuntu distribution..." -ForegroundColor Yellow
$distros = wsl --list --quiet 2>$null
if ($distros -notlike "*Ubuntu*") {
    Write-Host "Installing Ubuntu..." -ForegroundColor Yellow
    wsl --install -d Ubuntu --no-launch
    Write-Host "Ubuntu installed. Please restart, then run again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "Ubuntu is available." -ForegroundColor Green
Write-Host ""

# --- Step 3: Get wallet address from user ---
Write-Host "[3/6] Enter your RVN wallet address..." -ForegroundColor Yellow
Write-Host "It starts with 'R' and looks like: RWaPdLz6X5kVqN3vBnM8fGjKtQ2wErYcZx" -ForegroundColor Gray
$wallet = Read-Host "WALLET ADDRESS"
while ($wallet -notmatch '^R[a-zA-Z0-9]{34}$') {
    Write-Host "Invalid address. It must start with R and be 35 characters." -ForegroundColor Red
    $wallet = Read-Host "WALLET ADDRESS"
}
Write-Host "Wallet: $wallet" -ForegroundColor Green
Write-Host ""

# --- Step 4: Get card info (for reference only) ---
Write-Host "[4/6] Enter your card last 4 digits (for records)..." -ForegroundColor Yellow
Write-Host "This is just for your reference. We do NOT store your card data." -ForegroundColor Gray
$cardLast4 = Read-Host "CARD LAST 4 DIGITS (or press Enter to skip)"
Write-Host "Card ending in: $cardLast4" -ForegroundColor Green
Write-Host ""

# --- Step 5: Clone and configure ---
Write-Host "[5/6] Cloning and configuring mining setup..." -ForegroundColor Yellow
wsl -d Ubuntu bash -c "rm -rf /tmp/my-mining-server; git clone https://github.com/maxxxxx55555/main.git /tmp/my-mining-server"
wsl -d Ubuntu bash -c "cd /tmp/my-mining-server/my-mining-server && cp .env.example .env && sed -i ""s/your_rvn_wallet_address_here/$wallet/"" .env"
Write-Host "Configuration complete." -ForegroundColor Green
Write-Host ""

# --- Step 6: Run setup and start ---
Write-Host "[6/6] Running setup (this takes 10-30 minutes)..." -ForegroundColor Yellow
Write-Host "Sit back and watch the progress..." -ForegroundColor Gray
Write-Host ""

wsl -d Ubuntu bash -c "cd /tmp/my-mining-server/my-mining-server && sudo bash setup.sh"

Write-Host ""
Write-Host "Starting miner..." -ForegroundColor Yellow
wsl -d Ubuntu bash -c "sudo systemctl start miner"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  MINING IS NOW RUNNING" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Check status:" -ForegroundColor White
Write-Host "  wsl -d Ubuntu bash -c 'sudo systemctl status miner'" -ForegroundColor Gray
Write-Host ""
Write-Host "Check logs:" -ForegroundColor White
Write-Host "  wsl -d Ubuntu bash -c 'sudo journalctl -u miner -f'" -ForegroundColor Gray
Write-Host ""
Write-Host "Check GPU:" -ForegroundColor White
Write-Host "  wsl -d Ubuntu bash -c 'nvidia-smi'" -ForegroundColor Gray
Write-Host ""
Write-Host "Check earnings at: https://2miners.com/profile" -ForegroundColor White
Write-Host ""
Write-Host "To withdraw to your card ending in $cardLast4:" -ForegroundColor White
Write-Host "  1. Use Binance.com or Bybit.com" -ForegroundColor Gray
Write-Host "  2. Sell RVN for RUB" -ForegroundColor Gray
Write-Host "  3. Withdraw to your card" -ForegroundColor Gray
Write-Host ""
Write-Host "See WITHDRAW.md and WITHOUT_IP.md in the repo for full instructions." -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to close"