#!/usr/bin/env python3
"""Full legit traffic (proposal 2.3): session churn + controller deauth +
inactivity deauth + wrong-key auth failures. Load sets client count AND churn.
usage: legit_traffic.py --load {low,moderate,high} --duration SECONDS
"""
import argparse, os, random, subprocess, threading, time
HERE = os.path.dirname(os.path.abspath(__file__))
HCLI = ["sudo","hostapd_cli","-p","/run/hostapd"]
APS = {"wlan0": None, "wlan34": None}  #iface -> bssid, fille din main()
LOAD = {"low": (10,(60,120)), "moderate": (20,(20,40)), "high": (30,(5,15))}
CTRL_REASONS = [1,2,3,5]; INACT_REASON = 4; ROAM_REASON =3
def sh(*c): subprocess.run(c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def out(*c): return subprocess.run(c, capture_output=True, text=True).stdout
def mac(i):
    with open(f"/sys/class/net/{i}/address") as f: return f.read().strip()
def start(i,conf): sh("sudo","wpa_supplicant","-B","-i",i,"-c",conf)
def stop(i): sh("sudo","pkill","-f",f"wpa_supplicant -B -i {i} ")
def client_bssid(i):
     for line in out("sudo","wpa_cli","-i",i,"status").splitlines():
         if line.startswith("bssid="): return line.split("=",1)[1].strip().lower()
     return ""
def churn(i,lo,hi,end):
    time.sleep(random.uniform(0,min(10,hi)))
    while time.time()<end:
        time.sleep(random.uniform(lo,hi))
        if time.time()>=end: break
        sh("sudo","wpa_cli","-i",i,"disconnect"); time.sleep(random.uniform(2,5))
        sh("sudo","wpa_cli","-i",i,"reconnect")
def ap_deauths(cl,end):
    aps=list(APS)
    while time.time()<end:
        time.sleep(random.uniform(3,8))
        if time.time()>=end: break
        m=mac(random.choice(cl)); ap=random.choice(aps)
        if random.random()<0.3: sh(*HCLI,"-i",ap,"disassociate",m,f"reason={INACT_REASON}")
        else: sh(*HCLI,"-i",ap,"deauthenticate",m,f"reason={random.choice(CTRL_REASONS)}")
def roam(cl,end):
    b1,b2=APS["wlan0"],APS["wlan34"]
    while time.time()<end:
          time.sleep(random.uniform(8,16))
          if time.time()>=end: break
          c=random.choice(cl); cur=client_bssid(c)
          if cur==b1: ap,tgt="wlan0",b2
          elif cur==b2: ap,tgt="wlan34",b1
          else: continue
          sh(*HCLI,"-i",ap,"deauthenticate",mac(c),f"reason={ROAM_REASON}")
          time.sleep(0.3); sh("sudo","wpa_cli","-i",c,"roam",tgt)
def badkey(end):
    i="wlan31"; start(i, os.path.join(HERE,"wpa_bad.conf"))
    while time.time()<end:
        time.sleep(random.uniform(10,20)); sh("sudo","wpa_cli","-i",i,"reassociate")
    stop(i)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--load",choices=LOAD,required=True)
    ap.add_argument("--duration",type=int,required=True); a=ap.parse_args()
    for i in APS: APS[i]=mac(i)
    n,(lo,hi)=LOAD[a.load]; good=[f"wlan{i}" for i in range(1,n+1)]
    conf=os.path.abspath(os.path.join(HERE,"..","testbed","wpa_supplicant.conf"))
    end=time.time()+a.duration
    for c in good: start(c,conf)
    time.sleep(min(10,a.duration))
    ts=[threading.Thread(target=churn,args=(c,lo,hi,end)) for c in good]
    ts.append(threading.Thread(target=ap_deauths,args=(good,end)))
    ts.append(threading.Thread(target=roam,args=(good,end)))
    ts.append(threading.Thread(target=badkey,args=(end,)))
    for t in ts: t.start()
    for t in ts: t.join()
    for c in good: stop(c)
if __name__=="__main__": main()
