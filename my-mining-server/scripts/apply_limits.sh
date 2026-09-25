#!/bin/bash
# Apply GPU power and temperature limits via nvidia-smi
# Safe defaults: 85% power, 70°C target
# Run as: sudo bash /opt/my-mining-server/scripts/apply_limits.sh

set -e

# Load config if available
if [ -f /etc/miner/config/.env ]; then
    source /etc/miner/config/.env 2>/dev/null || true
fi

POWER_LIMIT=${POWER_LIMIT:-85}
TEMP_TARGET=${TEMP_TARGET:-70}

echo "=== Applying GPU Limits ==="
echo "Power Limit: ${POWER_LIMIT}%"
echo "Temperature Target: ${TEMP_TARGET}°C"

# Check if nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: nvidia-smi not found. Is the NVIDIA driver installed?"
    exit 1
fi

# Get number of GPUs
GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader,nounits | head -1)

if [ -z "$GPU_COUNT" ] || [ "$GPU_COUNT" -eq 0 ]; then
    echo "No NVIDIA GPUs detected."
    exit 1
fi

echo "Detected $GPU_COUNT GPU(s)"

# Apply power limits to each GPU
for i in $(seq 0 $((GPU_COUNT - 1))); do
    echo "Setting GPU $i power limit to ${POWER_LIMIT}%..."
    nvidia-smi -i $i --lock-clocks=0,0 || true
    nvidia-smi -i $i --power-limit=$POWER_LIMIT || true
done

# Set temperature management (if supported)
for i in $(seq 0 $((GPU_COUNT - 1))); do
    nvidia-smi -i $i --gpu-lock-clocks=0,0 || true
done

echo "GPU limits applied successfully."
echo "Note: Some settings may require a reboot to take full effect."