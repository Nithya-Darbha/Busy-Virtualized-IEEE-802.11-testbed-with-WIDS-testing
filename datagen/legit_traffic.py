#!/usr/bin/env python3
"""Legitimate client behaviour for 300 clients (wlan100 to wlan399):
cycles connect -> stay -> disconnect -> reconnect with jittered timing.
usage: legit_traffic.py --load <low|moderate|high> --duration <seconds>
"""
import argparse
import random
import subprocess
import threading
import time

CLIENT_START = 100
NUM_CLIENTS = 300
CLIENTS = [f"wlan{i}" for i in range(CLIENT_START, CLIENT_START + NUM_CLIENTS)]

SESSION = {
    "low": (60, 120),
    "moderate": (20, 40),
    "high": (5, 15)
}

def wpa(iface, *cmd):
    subprocess.run(
        ["wpa_cli", "-p", "/run/wpa_supplicant", "-i", iface, *cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def drive(iface, lo, hi, end):
    # Slumpmässig startförskjutning så att inte 300 klienter agerar samtidigt
    initial_delay = random.uniform(0, min(10, hi))
    time.sleep(initial_delay)

    while time.time() < end:
        sleep_dur = random.uniform(lo, hi)
        if time.time() + sleep_dur >= end:
            break
        time.sleep(sleep_dur)

        # Klienten kopplar ner
        wpa(iface, "disconnect")
        time.sleep(random.uniform(2, 5))

        if time.time() >= end:
            break

        # Klienten återansluter till sin AP
        wpa(iface, "reconnect")

def main():
    ap = argparse.ArgumentParser(description="Simulate legitimate 802.11 traffic for 300 clients.")
    ap.add_argument("--load", choices=SESSION.keys(), required=True, help="Traffic churn load level")
    ap.add_argument("--duration", type=int, required=True, help="Duration in seconds")
    a = ap.parse_args()

    lo, hi = SESSION[a.load]
    end = time.time() + a.duration

    print(f"[*] Starting legitimate traffic for {len(CLIENTS)} clients (load: {a.load}, duration: {a.duration}s)...")
    threads = []
    for c in CLIENTS:
        t = threading.Thread(target=drive, args=(c, lo, hi, end), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("[*] Legitimate traffic generation completed.")

if __name__ == "__main__":
    main()
