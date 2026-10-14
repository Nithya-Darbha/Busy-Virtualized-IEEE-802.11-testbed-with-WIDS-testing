#!/usr/bin/env python3

import sys, os, numpy as np, pandas as pd 
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
CSV=sys.argv[1] if len(sys.argv)>1 else os.path.join(ROOT,"data","processed","features.csv")
RES=os.path.join(ROOT,"results"); os.makedirs(RES,exist_ok=True) 
LO,HI=4,8 #deuah cout between 4-8 seconds (restrict window to have simailr deauth count)

FEATS=["n_deauth","n_src","src_entropy","iat_cv","reason_entropy","deauth_reassoc_ratio","frac_src_bssid"]
LABELS={"n_deauth":"deauth count","n_src":"distinct sources","src_entropy":"source entropy",
      "iat_cv":"inter-arrival CV","reason_entropy":"reason-code entropy",
      "deauth_reassoc_ratio":"deauth/reassoc ratio","frac_src_bssid":"frac from AP BSSID *"}
df=pd.read_csv(CSV)
band=df[(df.n_deauth>=LO)&(df.n_deauth<=HI)].copy()
att=band[band.label==1]; nor=band[band.label==0]
print(f"matched-volume band n_deauth in [{LO},{HI}]: {len(att)} attack, {len(nor)} normal windows\n")


rows=[]
for f in FEATS:
    auc=roc_auc_score(band["label"].values, band[f].values)
    rows.append(dict(feature=LABELS[f], legit_median=round(nor[f].median(),3),
                     attack_median=round(att[f].median(),3), separability=round(max(auc,1-auc),3)))
tab=pd.DataFrame(rows).sort_values("separability",ascending=False)
tab.to_csv(os.path.join(RES,"rq1_matched_volume.csv"),index=False)
print(tab.to_string(index=False))
print("\n* frac_src_bssid is the label-revealing feature (used only in RQ3), shown for reference.")

plot_feats=[f for f in FEATS if f!="frac_src_bssid"]
fig,axs=plt.subplots(2,3,figsize=(12,7))
for ax,f in zip(axs.ravel(),plot_feats):
    ax.boxplot([nor[f].values,att[f].values],tick_labels=["legit","attack"],showfliers=False,
               patch_artist=True,boxprops=dict(facecolor="#cfe3f2"),medianprops=dict(color="black"))
    for i,(d,c) in enumerate([(nor[f],"#4C78A8"),(att[f],"#E45756")],1):
        ax.scatter(np.random.normal(i,0.05,len(d)),d,s=5,alpha=.25,color=c)
    ax.set_title(LABELS[f],fontsize=11); ax.grid(True,axis="y",alpha=.3)
for ax in axs.ravel()[len(plot_feats):]: ax.axis("off")
fig.suptitle(f"RQ1: feature distributions at matched volume (deauth count in [{LO},{HI}])",fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(RES,"fig_rq1_distributions.png"),dpi=150); plt.close(fig)
print(f"\nrq1_matched_volume.csv, fig_rq1_distributions.png written to {RES}")
