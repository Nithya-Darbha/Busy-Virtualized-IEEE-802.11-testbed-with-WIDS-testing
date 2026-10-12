#!/usr/bin/env python3
"""Windowed feature extraction from the capture grid.
For every 1 s window of each pcap in data/raw/, computes:
  count      : n_deauth
  structural : n_disassoc, n_src, src_entropy, iat_cv
  semantic   : reason_entropy, deauth_reassoc_ratio
  label-revealing (RQ3 only) : frac_src_bssid
Each window is labelled attack/normal from the matching .gt log.
usage: extract.py [raw_dir] [out_csv]   (defaults: data/raw  data/processed/features.csv)
"""
import sys, os, glob, subprocess, math, csv
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "raw")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "processed", "features.csv")
W = 1.0

def entropy(c):
    t = sum(c.values())
    return 0.0 if t == 0 else -sum((v/t)*math.log2(v/t) for v in c.values())

def gt(pcap):
    g = pcap[:-5] + ".gt"; on = off = None; bssid = ""
    try:
        for line in open(g):
            kv = dict(p.split("=",1) for p in line.split() if "=" in p)
            if "attacker_on" in kv:
                on = kv.get("attacker_on","").strip() or None
                off = kv.get("attacker_off","").strip() or None
            if "bssid" in kv: bssid = kv["bssid"].strip().lower()
    except FileNotFoundError:
        pass
    return (float(on) if on else None, float(off) if off else None, bssid)

def rows(pcap):
    cmd = ["tshark","-r",pcap,"-Y",
     "wlan.fc.type==0 && (wlan.fc.subtype==12||wlan.fc.subtype==10||wlan.fc.subtype==2||wlan.fc.subtype==0)",
     "-T","fields","-e","frame.time_epoch","-e","wlan.fc.subtype","-e","wlan.sa",
     "-e","wlan.fixed.reason_code","-E","separator=|"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    for ln in p.stdout.splitlines():
        f = ln.split("|")
        if len(f) < 4: continue
        try: t = float(f[0])
        except ValueError: continue
        yield t, f[1].strip(), f[2].strip().lower(), f[3].strip()

out = []
for pcap in sorted(glob.glob(os.path.join(RAW, "*.pcap"))):
    base = os.path.basename(pcap)[:-5]
    try:
        rate = base.split("_")[0].split("-",1)[1]
        load = base.split("_")[1].split("-",1)[1]
    except IndexError:
        continue
    a_on, a_off, bssid = gt(pcap)
    data = list(rows(pcap))
    if not data:
        print(f"  {base}: no frames, skipped"); continue
    t0 = min(r[0] for r in data); tend = max(r[0] for r in data)
    nb = int((tend - t0)//W) + 1
    buck = [[] for _ in range(nb)]
    for t, st, sa, rc in data:
        b = int((t - t0)//W)
        if 0 <= b < nb: buck[b].append((t, st, sa, rc))
    for b, items in enumerate(buck):
        cen = t0 + (b + 0.5)*W
        disc = [x for x in items if x[1] in ("12","10")]
        nd = sum(1 for x in items if x[1] == "12")
        ndis = sum(1 for x in items if x[1] == "10")
        nre = sum(1 for x in items if x[1] in ("2","0"))
        srcs = Counter(x[2] for x in disc if x[2])
        reasons = Counter(x[3] for x in disc if x[3])
        tv = sorted(x[0] for x in disc)
        if len(tv) >= 2:
            ia = [j - i for i, j in zip(tv, tv[1:])]; m = sum(ia)/len(ia)
            cv = (sum((i-m)**2 for i in ia)/len(ia))**.5/m if m > 0 else 0.0
        else:
            cv = 0.0
        nn = len(disc)
        fb = (sum(1 for x in disc if x[2] == bssid)/nn) if nn and bssid else 0.0
        lab = 1 if (rate != "none" and a_on and a_off and a_on <= cen <= a_off) else 0
        out.append(dict(cell=base, rate=rate, load=load, win=round(b*W,1),
            n_deauth=nd, n_disassoc=ndis, n_src=len(srcs),
            src_entropy=round(entropy(srcs),4), iat_cv=round(cv,4),
            reason_entropy=round(entropy(reasons),4),
            deauth_reassoc_ratio=round(nd/(nre+1),4),
            frac_src_bssid=round(fb,4), label=lab))
    na = sum(1 for r in out if r['cell'] == base and r['label'] == 1)
    tot = sum(1 for r in out if r['cell'] == base)
    print(f"  {base}: {len(data)} frames  attack_win={na}  normal_win={tot-na}")

if not out:
    print("no windows produced, check data/raw/"); sys.exit(1)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
pos = sum(1 for r in out if r['label'] == 1)
print(f"\n{len(out)} windows -> {OUT}")
print(f"attack windows: {pos} ({100*pos/len(out):.1f}%)  normal: {len(out)-pos}")
