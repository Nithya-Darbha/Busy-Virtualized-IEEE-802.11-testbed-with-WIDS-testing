#!/usr/bin/env bash
# Bring up the hwsim testbed: 1 AP, 3 clients, 1 attacker, 1 monitor.
set -euo pipefail
# TODO: rfkill unblock; modprobe mac80211_hwsim radios=6; set ifaces unmanaged;
#       start hostapd + 3x wpa_supplicant; wlan4/wlan5 -> monitor on channel 6.
echo "TODO: implement up.sh"
