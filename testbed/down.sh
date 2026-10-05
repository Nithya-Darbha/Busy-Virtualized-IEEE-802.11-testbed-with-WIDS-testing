#!/usr/bin/env bash
set -uo pipefail

echo "[*] Stopping hostapd and wpa_supplicant..."
sudo killall -9 hostapd 2>/dev/null || true
sudo killall -9 wpa_supplicant 2>/dev/null || true

echo "[*] Bringing down all wlan interfaces..."
for iface in $(ip -o link show 2>/dev/null | awk -F': ' '{print $2}' | grep '^wlan' || true); do
  sudo ip link set "$iface" down 2>/dev/null || true
done

echo "[*] Removing temporary configs..."
sudo rm -rf /tmp/testbed_conf /run/hostapd /run/wpa_supplicant

echo "[*] Removing NetworkManager override..."
sudo rm -f /etc/NetworkManager/conf.d/99-hwsim-unmanaged.conf
sudo systemctl reload NetworkManager 2>/dev/null || true

echo "[*] Unloading mac80211_hwsim..."
sudo modprobe -r mac80211_hwsim 2>/dev/null || true

echo "[*] Testbed is down."
