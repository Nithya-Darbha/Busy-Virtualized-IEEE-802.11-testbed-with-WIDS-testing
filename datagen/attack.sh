#!/usr/bin/env bash
# usage: attack.sh <low|moderate|high> <duration> <bssid> <iface>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
case "$1" in low) PPS=5;; moderate) PPS=50;; high) PPS=200;; *) echo "bad rate"; exit 1;; esac
sudo python3 "$HERE/attack.py" "$4" "$3" "$PPS" "$2"
