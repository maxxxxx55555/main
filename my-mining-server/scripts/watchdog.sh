#!/bin/bash
# Mining Watchdog Script
# Monitors: miner process, GPU temperature, hashrate
# Run as: root via cron (systemctl restart requires root)
# systemd service already has Restart=always for crash recovery

set -e

# Paths
SCRIPT_DIR="/opt/my-mining-server"
LOG_FILE="/var/log/miner/watchdog.log"

# Ensure log directory exists
mkdir -p /var/log/miner
touch "$LOG_FILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Load config if available
if [ -f /etc/miner/config/.env ]; then
    source /etc/miner/config/.env 2>/dev/null || true
fi

API_PORT=${API_PORT:-4068}
TEMP_TARGET=${TEMP_TARGET:-70}

# Check if miner process is running
check_miner_process() {
    if pgrep -f "trex" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Check GPU temperature
check_gpu_temp() {
    if ! command -v nvidia-smi &> /dev/null; then
        echo "0"
        return
    fi
    
    local max_temp=0
    while IFS= read -r line; do
        local temp=$(echo "$line" | awk '{print $1}')
        if [ "$temp" -gt "$max_temp" ]; then
            max_temp=$temp
        fi
    done < <(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits)
    
    echo "$max_temp"
}

# Check hashrate via API (if available)
check_hashrate() {
    if ! command -v curl &> /dev/null; then
        echo "0"
        return
    fi
    
    local response=$(curl -s http://localhost:${API_PORT}/api/v1/status 2>/dev/null || echo "")
    if [ -n "$response" ]; then
        echo "$response" | grep -oP '"hashrate":\s*\K[0-9.]+' | head -1 || echo "0"
    else
        echo "0"
    fi
}

# Main monitoring loop
log "=== Watchdog Check ==="

# Check miner process
if check_miner_process; then
    log "Miner process: RUNNING"
else
    log "WARNING: Miner process NOT RUNNING - systemd will auto-restart (Restart=always)"
fi

# Check GPU temperature
MAX_TEMP=$(check_gpu_temp)
log "Max GPU temperature: ${MAX_TEMP}°C"

if [ "$MAX_TEMP" -gt "$TEMP_TARGET" ]; then
    log "WARNING: GPU temperature exceeds target (${TEMP_TARGET}°C)"
fi

if [ "$MAX_TEMP" -gt 85 ]; then
    log "WARNING: GPU temperature high (${MAX_TEMP}°C) - check cooling"
fi

# Check hashrate
HASHRATE=$(check_hashrate)
log "Hashrate: ${HASHRATE} H/s"

if [ "$HASHRATE" = "0" ] || [ -z "$HASHRATE" ]; then
    log "WARNING: Could not read hashrate from API"
fi

log "=== Watchdog Check Complete ==="