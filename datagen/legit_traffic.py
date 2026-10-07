#!/usr/bin/env python3
"""Full legit traffic (proposal 2.3): session churn + controller deauth +
inactivity deauth + wrong-key auth failures. Load sets client count AND churn.
usage: legit_traffic.py --load {low,moderate,high} --duration SECONDS
"""
import argparse, os, random, subprocess, threading, time
HERE = os.path.dirname(os.path.abspath(__file__))
HCLI = ["sudo","hostapd_cli","-p","/run/hostapd"]
LOAD = {"low": (10,(60,120)), "moderate": (20,(20,40)), "high": (30,(5,15))}
CTRL_REASONS = [1,2,3,5]; INACT_REASON = 4
def sh(*c): subprocess.run(c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def mac(i):
    with open(f"/sys/class/net/{i}/address") as f: return f.read().strip()
def start(i,conf): sh("sudo","wpa_supplicant","-B","-i",i,"-c",conf)
def stop(i): sh("sudo","pkill","-f",f"wpa_supplicant -B -i {i} ")
def churn(i,lo,hi,end):
    time.sleep(random.uniform(0,min(10,hi)))
    while time.time()<end:
        time.sleep(random.uniform(lo,hi))
        if time.time()>=end: break
        sh("sudo","wpa_cli","-i",i,"disconnect"); time.sleep(random.uniform(2,5))
        sh("sudo","wpa_cli","-i",i,"reconnect")
def ap_deauths(cl,end):
    while time.time()<end:
        time.sleep(random.uniform(3,8))
        if time.time()>=end: break
        m=mac(random.choice(cl))
        if random.random()<0.3: sh(*HCLI,"disassociate",m,f"reason={INACT_REASON}")
        else: sh(*HCLI,"deauthenticate",m,f"reason={random.choice(CTRL_REASONS)}")
def badkey(end):
    i="wlan31"; start(i, os.path.join(HERE,"wpa_bad.conf"))
    while time.time()<end:
        time.sleep(random.uniform(10,20)); sh("sudo","wpa_cli","-i",i,"reassociate")
    stop(i)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--load",choices=LOAD,required=True)
    ap.add_argument("--duration",type=int,required=True); a=ap.parse_args()
    n,(lo,hi)=LOAD[a.load]; good=[f"wlan{i}" for i in range(1,n+1)]
    conf=os.path.abspath(os.path.join(HERE,"..","testbed","wpa_supplicant.conf"))
    end=time.time()+a.duration
    for c in good: start(c,conf)
    time.sleep(min(10,a.duration))
    ts=[threading.Thread(target=churn,args=(c,lo,hi,end)) for c in good]
    ts.append(threading.Thread(target=ap_deauths,args=(good,end)))
    ts.append(threading.Thread(target=badkey,args=(end,)))
    for t in ts: t.start()
    for t in ts: t.join()
    for c in good: stop(c)
if __name__=="__main__": main()
