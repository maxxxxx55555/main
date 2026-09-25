# Security Checklist

## Secrets Management
- [ ] Never commit `.env` file to git (it is in `.gitignore`)
- [ ] Use `.env.example` as template only
- [ ] Set `chmod 600 /etc/miner/config/.env` after editing
- [ ] Set `chown miner:miner /etc/miner/config/.env`
- [ ] Never share your wallet address publicly (it is public anyway, but keep seed phrase secret)
- [ ] Never share your 12-word seed phrase with anyone
- [ ] Store seed phrase on paper, offline, in a safe place

## User Permissions
- [ ] Miner runs as `miner` user (non-root)
- [ ] Miner user has `video` and `input` group membership
- [ ] Miner user cannot modify system files
- [ ] Root access required only for setup and management commands

## Firewall
- [ ] Enable UFW: `sudo ufw enable`
- [ ] Allow SSH only: `sudo ufw allow ssh`
- [ ] Allow miner pool ports: `sudo ufw allow 4444`
- [ ] Allow T-Rex API port: `sudo ufw allow 4068`
- [ ] Deny all other inbound: `sudo ufw default deny incoming`

## Package Sources
- [ ] Use only official Ubuntu repositories: `apt-get`
- [ ] Use only official NVIDIA driver: `apt-get install nvidia-driver-*`
- [ ] Use only official T-Rex release: https://github.com/trexminer/trex/releases
- [ ] Verify checksums if available (T-Rex does not provide checksums by default)

## System Updates
- [ ] Update system regularly: `sudo apt-get update && sudo apt-get upgrade -y`
- [ ] Update T-Rex when new version is released
- [ ] Reboot after kernel updates if required

## Process Monitoring
- [ ] Check running processes: `ps aux | grep trex`
- [ ] Verify no suspicious processes: `ps aux`
- [ ] Check open ports: `sudo netstat -tulpn`
- [ ] Monitor GPU usage: `nvidia-smi`

## Data Privacy
- [ ] Miner does not collect personal data
- [ ] Pool only receives your wallet address and hashrate
- [ ] No keyloggers or spyware installed
- [ ] No background data collection

## Incident Response
If you suspect compromise:
1. Stop the miner: `sudo systemctl stop miner`
2. Check logs: `sudo journalctl -u miner -n 100`
3. Check for unknown processes: `ps aux`
4. Change all passwords
5. Restore from known good backup
6. Reinstall system if necessary