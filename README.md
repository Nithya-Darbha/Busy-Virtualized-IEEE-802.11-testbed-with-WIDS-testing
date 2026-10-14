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



## Environment
Kali (ARM64) VM, mac80211_hwsim software radios. Attacks run only against the
local emulated network.
