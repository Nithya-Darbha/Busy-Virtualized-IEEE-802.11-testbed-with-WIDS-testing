#!/usr/bin/env bash
# Bring up testbed: 30 APs (wlan0-29), 300 clients (wlan100-399),
# attacker (wlan30), monitor (wlan31) using 100 hwsim radios.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

NUM_APS=30
NUM_CLIENTS=300
CH=6

ATTACKER="wlan30"
MONITOR="wlan31"
CONF_DIR="/tmp/testbed_conf"

echo "[*] 1. Cleaning previous processes and interfaces..."
sudo killall -9 tcpdump hostapd wpa_supplicant 2>/dev/null || true

for iface in $(ip -o link show 2>/dev/null | awk -F': ' '{print $2}' | grep '^wlan' || true); do
  sudo ip link set "$iface" down 2>/dev/null || true
done
sleep 1

echo "[*] 2. Unloading mac80211_hwsim, mac80211 and cfg80211..."
if lsmod | grep -q "^mac80211_hwsim"; then
  sudo modprobe -r mac80211_hwsim
fi
# Laddar ur cfg80211 för att nollställa wiphy-räknaren
sudo modprobe -r mac80211 cfg80211 2>/dev/null || true
sleep 1

echo "[*] 3. Configuring NetworkManager to ignore all wlan interfaces..."
sudo mkdir -p /etc/NetworkManager/conf.d
echo -e "[keyfile]\nunmanaged-devices=interface-name:wlan*" | sudo tee /etc/NetworkManager/conf.d/99-hwsim-unmanaged.conf > /dev/null
sudo systemctl reload NetworkManager 2>/dev/null || true

echo "[*] 4. Loading mac80211_hwsim with 100 radios..."
sudo rfkill unblock all || true
sudo modprobe mac80211_hwsim radios=100
sleep 2

rm -rf "$CONF_DIR"
mkdir -p "$CONF_DIR/hostapd" "$CONF_DIR/wpa"
sudo mkdir -p /run/hostapd /run/wpa_supplicant

echo "[*] 5. Detecting actual PHY names dynamically..."
ALL_PHYS=($(iw list | grep '^Wiphy' | awk '{print $2}'))
echo "[+] Hittade ${#ALL_PHYS[@]} radioenheter (${ALL_PHYS[0]} till ${ALL_PHYS[-1]})."

echo "[*] 6. Starting 30 APs (wlan0..wlan29)..."
for i in $(seq 0 $((NUM_APS - 1))); do
  cat <<EOF > "$CONF_DIR/hostapd/hostapd_wlan${i}.conf"
interface=wlan${i}
driver=nl80211
ctrl_interface=/run/hostapd
ssid=testbed
hw_mode=g
channel=${CH}
wpa=2
wpa_passphrase=testbed123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF
  sudo hostapd -B "$CONF_DIR/hostapd/hostapd_wlan${i}.conf" >/dev/null 2>&1
done

sleep 2

echo "[*] 7. Reading AP BSSIDs..."
declare -a AP_BSSIDS
for i in $(seq 0 $((NUM_APS - 1))); do
  AP_BSSIDS[$i]=$(cat "/sys/class/net/wlan${i}/address")
done

echo "[*] 8. Creating 300 virtual client interfaces (wlan100..wlan399)..."
# Vi fördelar klienterna jämnt över 30 klient-radios (från radio index 32 till 61)
for k in $(seq 0 $((NUM_CLIENTS - 1))); do
  phy_idx=$((32 + (k % 30)))
  target_phy="${ALL_PHYS[$phy_idx]}"
  iface="wlan$((100 + k))"
  
  # Generera en unik, deterministisk MAC-adress
  b1=$((k / 256))
  b2=$((k % 256))
  mac=$(printf "02:00:00:01:%02x:%02x" "$b1" "$b2")

  sudo iw phy "$target_phy" interface add "$iface" type managed addr "$mac"
  sudo ip link set "$iface" up
done

echo "[*] 9. Starting wpa_supplicant for all 300 clients (10 per AP)..."
for k in $(seq 0 $((NUM_CLIENTS - 1))); do
  iface="wlan$((100 + k))"
  ap_idx=$((k % NUM_APS))
  target_bssid="${AP_BSSIDS[$ap_idx]}"

  cat <<EOF > "$CONF_DIR/wpa/wpa_${iface}.conf"
ctrl_interface=/run/wpa_supplicant
network={
    ssid="testbed"
    bssid=${target_bssid}
    psk="testbed123"
    key_mgmt=WPA-PSK
}
EOF
  sudo wpa_supplicant -B -i "$iface" -c "$CONF_DIR/wpa/wpa_${iface}.conf" >/dev/null 2>&1

  if [ $(( (k + 1) % 50 )) -eq 0 ]; then
    echo "    - $((k + 1)) / $NUM_CLIENTS klienter startade..."
    sleep 0.5
  fi
done

echo "[*] 10. Waiting for client associations..."
for t in $(seq 1 40); do
  assoc_count=0
  for i in $(seq 0 $((NUM_APS - 1))); do
    c=$(sudo iw dev "wlan${i}" station dump 2>/dev/null | grep -c '^Station' || true)
    assoc_count=$((assoc_count + c))
  done
  echo "    [$t/40s] Associerade klienter: $assoc_count / $NUM_CLIENTS"
  if [ "$assoc_count" -ge "$((NUM_CLIENTS * 95 / 100))" ]; then
    echo "[*] Klienter framgångsrikt associerade ($assoc_count/$NUM_CLIENTS)."
    break
  fi
  sleep 1
done

echo "[*] 11. Setting monitor mode on attacker ($ATTACKER) and monitor ($MONITOR)..."
for iface in "$ATTACKER" "$MONITOR"; do
  sudo ip link set "$iface" down
  sudo iw dev "$iface" set type monitor
  sudo ip link set "$iface" up
  sudo iw dev "$iface" set channel "$CH"
done

echo
echo "=========================================================="
echo " Testbädd uppe:"
echo " - APs:      wlan0 - wlan29 (30 st, SSID 'testbed')"
echo " - Klienter: wlan100 - wlan399 (300 st, 10 per AP)"
echo " - Attacker: $ATTACKER (monitor mode, ch $CH)"
echo " - Monitor:  $MONITOR (monitor mode, ch $CH)"
echo "=========================================================="
