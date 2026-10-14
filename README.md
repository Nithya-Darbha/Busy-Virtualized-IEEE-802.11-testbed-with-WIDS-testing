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
```bash
sudo apt update
sudo apt install -y
sudo apt install -y hostapd wpasupplicant iw tcpdump tshark rfkill network-manager
xsudo apt install -y python3-scapy python3-sklearn python3-pandas python3-numpy python3-matplotlib
```
The virtual Wi-Fi radios (`mac80211_hwsim`) are built into Linux, `testbed/up.sh` brings them up automatically.

## Reproduce
```bash
sudo bash testbed/up.sh # bring up the virtual networks(2 AP's , clients, monitor) 
sudo bash datagen/run_grid.sh #generate 4*3 attacker-rate x network load capture grid 
python3 features/extract.py # extract the features form the pcaps
python3 detect/rule_based.py # threshold detector (leave one capture out)
python3 detect/random_forest.py #random forest + RQ3 ablations
python3 eval/metrics.py # RQ2 plots + detector comparisions
python3 eval/rq1_analysis.py # matched volume feature analysis for RQ1

```
