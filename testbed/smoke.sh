#!/usr/bin/env bash
# Fire ONE deauth from the attacker, confirm the monitor captured it.
set -euo pipefail
PCAP=/tmp/smoke.pcap
BSSID=$(cat /sys/class/net/wlan0/address)
echo "[*] AP BSSID: $BSSID"

echo "[*] Capturing on wlan5 for 8s..."
sudo timeout 8 tcpdump -i wlan5 -e -s0 -w "$PCAP" 'type mgt subtype deauth' 2>/dev/null &
CAP_PID=$!
sleep 2

echo "[*] Firing one deauth from wlan4..."
sudo aireplay-ng --deauth 1 -a "$BSSID" --ignore-negative-one wlan4 || \
  sudo timeout 2 mdk4 wlan4 d -B "$BSSID" || true

wait $CAP_PID 2>/dev/null || true

N=$(sudo tcpdump -r "$PCAP" 2>/dev/null | grep -ci deauth || true)
echo
if [ "${N:-0}" -ge 1 ]; then
  echo "[PASS] captured $N deauth frame(s)."
else
  echo "[FAIL] no deauth captured. Check wlan4/wlan5 on channel 6 and clients associated."
fi
