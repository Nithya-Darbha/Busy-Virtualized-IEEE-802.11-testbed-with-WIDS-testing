#!/usr/bin/env python3
"""Legitimate client behaviour: each client cycles connect -> stay -> disconnect
-> reconnect with jittered timing. Load sets churn (shorter sessions = more
legitimate deauth/disassoc). usage: legit_traffic.py --load L --duration S
"""
import argparse, random, subprocess, threading, time

CLIENTS = ["wlan1", "wlan2", "wlan3"]
SESSION = {"low": (60, 120), "moderate": (20, 40), "high": (5, 15)}

def wpa(iface, *cmd):
    subprocess.run(["sudo", "wpa_cli", "-i", iface, *cmd],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def drive(iface, lo, hi, end):
    while time.time() < end:
        time.sleep(random.uniform(lo, hi))
        if time.time() >= end: break
        wpa(iface, "disconnect")
        time.sleep(random.uniform(2, 5))
        wpa(iface, "reconnect")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--load", choices=SESSION, required=True)
    ap.add_argument("--duration", type=int, required=True)
    a = ap.parse_args()
    lo, hi = SESSION[a.load]
    end = time.time() + a.duration
    ts = [threading.Thread(target=drive, args=(c, lo, hi, end)) for c in CLIENTS]
    for t in ts: t.start()
    for t in ts: t.join()

if __name__ == "__main__":
    main()
