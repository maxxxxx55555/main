# ============================================
#  BOT LAUNCHER - WINDOWS
#  One script to start Telegram bot
# ============================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  BOT SETUP - WINDOWS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: Check for WSL ---
Write-Host "[1/5] Checking for WSL..." -ForegroundColor Yellow
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
Write-Host "[2/5] Checking Ubuntu distribution..." -ForegroundColor Yellow
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

# --- Step 3: Get bot token ---
Write-Host "[3/5] Enter your Telegram bot token..." -ForegroundColor Yellow
Write-Host "Get it from @BotFather on Telegram: /newbot" -ForegroundColor Gray
$token = Read-Host "BOT TOKEN"
while ($token -notmatch '^\d{8,10}:[a-zA-Z0-9_-]{35}$') {
    Write-Host "Invalid token format." -ForegroundColor Red
    $token = Read-Host "BOT TOKEN"
}
Write-Host "Token: $($token.Substring(0, [Math]::Min(10, $token.Length)))..." -ForegroundColor Green
Write-Host ""

# --- Step 4: Get admin IDs ---
Write-Host "[4/5] Enter admin user IDs (comma separated, or press Enter for none)..." -ForegroundColor Yellow
Write-Host "Get your user ID from @userinfobot on Telegram" -ForegroundColor Gray
$admins = Read-Host "ADMIN IDS"
if ([string]::IsNullOrEmpty($admins)) {
    $admins = "0"
}
Write-Host "Admins: $admins" -ForegroundColor Green
Write-Host ""

# --- Step 5: Clone, configure, and launch ---
Write-Host "[5/5] Cloning, configuring, and launching bot..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

wsl -d Ubuntu bash -c "rm -rf /tmp/aibot; git clone https://github.com/maxxxxx55555/aibot.git /tmp/aibot"
wsl -d Ubuntu bash -c "cd /tmp/aibot && cp .env.example .env && sed -i \"s/BOT_TOKEN=.*/BOT_TOKEN=$token/\" .env && sed -i \"s/ADMIN_IDS=.*/ADMIN_IDS=$admins/\" .env"

# Check if docker-compose exists
$hasDocker = wsl -d Ubuntu bash -c "test -f /tmp/aibot/docker-compose.yml && echo yes"
if ($hasDocker -eq "yes") {
    Write-Host "Starting with Docker..." -ForegroundColor Yellow
    wsl -d Ubuntu bash -c "cd /tmp/aibot && sudo docker compose up -d --build"
} else {
    Write-Host "Starting with deploy.sh..." -ForegroundColor Yellow
    wsl -d Ubuntu bash -c "cd /tmp/aibot && sudo bash deploy.sh"
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  BOT IS NOW RUNNING" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Check status:" -ForegroundColor White
Write-Host "  wsl -d Ubuntu bash -c 'sudo systemctl status bot'" -ForegroundColor Gray
Write-Host ""
Write-Host "Check logs:" -ForegroundColor White
Write-Host "  wsl -d Ubuntu bash -c 'sudo journalctl -u bot -f'" -ForegroundColor Gray
Write-Host ""
Write-Host "Your bot should be live on Telegram now." -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to close"