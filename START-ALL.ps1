# ============================================
#  ALL-IN-ONE LAUNCHER - WINDOWS
#  Mining + Bot in one script
# ============================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  MINING + BOT - ONE SCRIPT" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: Check for WSL ---
Write-Host "[1/7] Checking for WSL..." -ForegroundColor Yellow
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
Write-Host "[2/7] Checking Ubuntu distribution..." -ForegroundColor Yellow
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

# --- Step 3: Get wallet address ---
Write-Host "[3/7] Enter your RVN wallet address..." -ForegroundColor Yellow
Write-Host "Get it from: https://ravencoin.com/ -> Get a Wallet" -ForegroundColor Gray
$wallet = Read-Host "WALLET ADDRESS"
while ($wallet -notmatch '^R[a-zA-Z0-9]{34}$') {
    Write-Host "Invalid. Must start with R and be 35 characters." -ForegroundColor Red
    $wallet = Read-Host "WALLET ADDRESS"
}
Write-Host "Wallet: $wallet" -ForegroundColor Green
Write-Host ""

# --- Step 4: Get card info ---
Write-Host "[4/7] Enter your card last 4 digits (for reference)..." -ForegroundColor Yellow
$cardLast4 = Read-Host "CARD LAST 4 DIGITS (or press Enter to skip)"
Write-Host "Card ending in: $cardLast4" -ForegroundColor Green
Write-Host ""

# --- Step 5: Get bot token ---
Write-Host "[5/7] Enter your Telegram bot token..." -ForegroundColor Yellow
Write-Host "Get it from @BotFather on Telegram: /newbot" -ForegroundColor Gray
$token = Read-Host "BOT TOKEN"
while ($token -notmatch '^\d{8,10}:[a-zA-Z0-9_-]{35}$') {
    Write-Host "Invalid token format." -ForegroundColor Red
    $token = Read-Host "BOT TOKEN"
}
Write-Host "Token: $($token.Substring(0, [Math]::Min(10, $token.Length)))..." -ForegroundColor Green
Write-Host ""

# --- Step 6: Get admin IDs ---
Write-Host "[6/7] Enter admin user IDs (comma separated, or Enter for none)..." -ForegroundColor Yellow
Write-Host "Get your user ID from @userinfobot on Telegram" -ForegroundColor Gray
$admins = Read-Host "ADMIN IDS"
if ([string]::IsNullOrEmpty($admins)) {
    $admins = "0"
}
Write-Host "Admins: $admins" -ForegroundColor Green
Write-Host ""

# --- Step 7: Clone, configure, and launch ---
Write-Host "[7/7] Cloning, configuring, and launching..." -ForegroundColor Yellow
Write-Host "This may take 10-30 minutes for mining setup..." -ForegroundColor Gray
Write-Host ""
# --- MINING ---
Write-Host ""
Write-Host ">>> Cloning mining repository..." -ForegroundColor Magenta
wsl -d Ubuntu bash -c "rm -rf /tmp/my-mining-server; git clone https://github.com/maxxxxx55555/main.git /tmp/my-mining-server"

Write-Host ">>> Configuring mining .env..." -ForegroundColor Magenta
wsl -d Ubuntu bash -c "cd /tmp/my-mining-server/my-mining-server && cp .env.example .env && env WALLET=$wallet bash -c 'sed -i \"\"s/your_rvn_wallet_address_here/$WALLET/\"\" .env'"

Write-Host ">>> Running mining setup (10-30 minutes)..." -ForegroundColor Magenta
Write-Host "    Please wait..." -ForegroundColor Gray
wsl -d Ubuntu bash -c "cd /tmp/my-mining-server/my-mining-server && sudo bash setup.sh"

Write-Host ">>> Starting miner..." -ForegroundColor Magenta
wsl -d Ubuntu bash -c "sudo systemctl start miner"

# --- BOT ---
Write-Host ""
Write-Host ">>> Cloning bot repository..." -ForegroundColor Magenta
wsl -d Ubuntu bash -c "rm -rf /tmp/aibot; git clone https://github.com/maxxxxx55555/aibot.git /tmp/aibot"

Write-Host ">>> Configuring bot .env..." -ForegroundColor Magenta
wsl -d Ubuntu bash -c "cd /tmp/aibot && cp .env.example .env && env TOKEN=$token ADMINS=$admins bash -c 'sed -i \"\"s/BOT_TOKEN=.*/BOT_TOKEN=$TOKEN/\"\" .env && sed -i \"\"s/ADMIN_IDS=.*/ADMIN_IDS=$ADMINS/\"\" .env'"

Write-Host ">>> Starting bot..." -ForegroundColor Magenta
$hasDocker = wsl -d Ubuntu bash -c "test -f /tmp/aibot/docker-compose.yml && echo yes"
if ($hasDocker -eq "yes") {
    Write-Host "    Using Docker..." -ForegroundColor Gray
    wsl -d Ubuntu bash -c "cd /tmp/aibot && sudo docker compose up -d --build"
} else {
    Write-Host "    Using deploy.sh..." -ForegroundColor Gray
    wsl -d Ubuntu bash -c "cd /tmp/aibot && sudo bash deploy.sh"
}

# --- DONE ---
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  ALL DONE - BOTH ARE RUNNING" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "MINING:" -ForegroundColor White
Write-Host "  Status:  wsl -d Ubuntu bash -c 'sudo systemctl status miner'" -ForegroundColor Gray
Write-Host "  Logs:    wsl -d Ubuntu bash -c 'sudo journalctl -u miner -f'" -ForegroundColor Gray
Write-Host "  GPU:     wsl -d Ubuntu bash -c 'nvidia-smi'" -ForegroundColor Gray
Write-Host "  Earnings: https://2miners.com/profile" -ForegroundColor Gray
Write-Host ""
Write-Host "BOT:" -ForegroundColor White
Write-Host "  Status:  wsl -d Ubuntu bash -c 'sudo systemctl status bot'" -ForegroundColor Gray
Write-Host "  Logs:    wsl -d Ubuntu bash -c 'sudo journalctl -u bot -f'" -ForegroundColor Gray
Write-Host ""
Write-Host "Your bot is live on Telegram." -ForegroundColor White
Write-Host "Your miner is earning RVN." -ForegroundColor White
Write-Host "Withdraw to your card ending in $cardLast4 via Binance/Bybit." -ForegroundColor White
Write-Host ""
Write-Host "Full instructions in the repo:" -ForegroundColor White
Write-Host "  https://github.com/maxxxxx55555/main" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to close"