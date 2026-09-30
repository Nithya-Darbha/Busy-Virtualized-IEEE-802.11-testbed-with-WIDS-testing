#!/usr/bin/env bash
set -uo pipefail
echo "[*] Stopping hostapd / wpa_supplicant..."
sudo pkill hostapd 2>/dev/null || true
sudo pkill wpa_supplicant 2>/dev/null || true
echo "[*] Removing hwsim radios..."
sudo modprobe -r mac80211_hwsim 2>/dev/null || true
echo "[*] Down."
