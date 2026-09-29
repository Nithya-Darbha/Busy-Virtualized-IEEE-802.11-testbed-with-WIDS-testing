# Virtualized IEEE 802.11 Testbed with WIDS Testing

Rule-based vs. random forest detection of deauthentication anomalies in busy
virtualised IEEE 802.11 networks. Course project, II2202 (KTH).

## Layout
- testbed/   hwsim bringup (AP, clients, attacker, monitor)
- datagen/   attacker-rate x traffic-load data-generation grid
- features/  pcap to windowed feature vectors
- detect/    rule-based and random forest detectors
- eval/      metrics (precision/recall/F1/FPR) and plots
- data/      raw captures + processed sets (gitignored)
- results/   figures and tables

## Environment
Kali (ARM64) VM, mac80211_hwsim software radios. Attacks run only against the
local emulated network.
