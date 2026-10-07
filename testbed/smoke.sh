#!/usr/bin/env bash
set -euo pipefail
BSSID=$(cat /sys/class/net/wlan0/address); PCAP=/tmp/smoke.pcap
echo "[*] AP BSSID: $BSSID"; echo "[*] Capturing on wlan33 for 8s..."
sudo timeout 8 tcpdump -i wlan33 -e -s0 -w "$PCAP" 'type mgt subtype deauth' 2>/dev/null & CAP=$!
sleep 2; echo "[*] Firing deauth from wlan32..."
sudo python3 "$(dirname "$0")/../datagen/attack.py" wlan32 "$BSSID" 10 2 || true
wait $CAP 2>/dev/null||true
N=$(sudo tcpdump -r "$PCAP" 2>/dev/null | grep -ci deauth || true)
if [ "${N:-0}" -ge 1 ]; then echo "[PASS] captured $N deauth."; else echo "[FAIL] none captured."; fi
