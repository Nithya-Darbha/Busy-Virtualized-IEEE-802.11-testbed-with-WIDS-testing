#!/usr/bin/env bash
# Bring up the hwsim testbed: AP=wlan0, clients=wlan1-3, attacker=wlan4, monitor=wlan5.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CH=6

echo "[*] Cleaning any previous run..."
sudo pkill hostapd 2>/dev/null || true
sudo pkill wpa_supplicant 2>/dev/null || true
sleep 1
sudo modprobe -r mac80211_hwsim 2>/dev/null || true
sleep 1

echo "[*] Loading 6 hwsim radios..."
sudo rfkill unblock all || true
sudo modprobe mac80211_hwsim radios=6
sleep 2

echo "[*] Taking wlan0-5 out of NetworkManager..."
for i in 0 1 2 3 4 5; do sudo nmcli dev set wlan$i managed no 2>/dev/null || true; done

echo "[*] Starting AP on wlan0..."
sudo hostapd -B "$HERE/hostapd.conf"
sleep 3

echo "[*] Starting clients wlan1, wlan2, wlan3..."
for i in 1 2 3; do sudo wpa_supplicant -B -i wlan$i -c "$HERE/wpa_supplicant.conf"; done
sleep 6

echo "[*] Waiting for clients to associate..."
for i in 1 2 3; do
  for t in $(seq 1 20); do
    state=$(sudo wpa_cli -i wlan$i status 2>/dev/null | grep -oP 'wpa_state=\K\w+' || true)
    [ "$state" = "COMPLETED" ] && break
    sleep 1
  done
done

echo "[*] Monitor mode on attacker(wlan4) + capture(wlan5), channel $CH..."
for i in 4 5; do
  sudo ip link set wlan$i down
  sudo iw dev wlan$i set type monitor
  sudo ip link set wlan$i up
  sudo iw dev wlan$i set channel $CH
done

BSSID=$(cat /sys/class/net/wlan0/address)
echo
echo "[*] AP BSSID: $BSSID"
echo "[*] Client links:"
for i in 1 2 3; do printf '  wlan%s: ' "$i"; iw dev wlan$i link | head -1; done
echo
echo "[*] Up. Attacker=wlan4  Monitor=wlan5  channel=$CH"
