
#!/usr/bin/env bash
#AP1 (wlan0) and AP2 (wlan34), up to 30 clients (wlan1-30), badkey wlan31, attacker wlan32, monitor wlan33.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CH=6; NRADIOS=35; ATT=wlan32; MON=wlan33
echo "[*] Reset..."; sudo pkill hostapd 2>/dev/null||true; sudo pkill wpa_supplicant 2>/dev/null||true
sleep 1; sudo modprobe -r mac80211_hwsim 2>/dev/null||true; sleep 1
echo "[*] Load $NRADIOS radios..."; sudo rfkill unblock all||true
sudo modprobe mac80211_hwsim radios=$NRADIOS; sleep 2
for d in /sys/class/net/wlan*; do sudo nmcli dev set "$(basename "$d")" managed no 2>/dev/null||true; done
echo "[*] AP1 on wlan0..."; sudo hostapd -B "$HERE/hostapd.conf"; sleep 3
echo "[*] AP2 on wlan34..."; sudo hostapd -B "$HERE/hostapd2.conf"; sleep 3
echo "[*] Monitor mode attacker=$ATT monitor=$MON..."
for IF in "$ATT" "$MON"; do
  sudo ip link set "$IF" down; sudo iw dev "$IF" set type monitor
  sudo ip link set "$IF" up; sudo iw dev "$IF" set channel $CH
done
echo "[*] AP1 BSSID: $(cat /sys/class/net/wlan0/address)"
echo "[*] AP2 BSSID: $(cat /sys/class/net/wlan34/address)"
echo "[*] Infra up. clients wlan1-30 (per cell), badkey wlan31, attacker $ATT, monitor $MON"
