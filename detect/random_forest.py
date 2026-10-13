#!/usr/bin/env python3
"""Random forest over the full feature set, plus the four ablation configs
(with/without label-revealing feature, with/without legit deauth in normal)."""


import sys, os, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, accuracy_score

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CSV = sys.argv[1] if len(sys.argv)>1 else os.path.join(ROOT, "data", "processed", "features.csv")
SEED=42
NTREES=300

COUNT=["n_deauth"]
STRUCT=["n_disassoc", "n_src", "src_entropy", "iat_cv"]
SEM =["reason_entropy" , "deauth_reassoc_ratio"]
MAIN= COUNT +STRUCT+ SEM
LABELREV = ["frac_src_bssid"]


def metrics(y, yh):
	p, r ,f , _= precision_recall_fscore_support(y,yh, average="binary", zero_division=0)
	tn , fp, fn,tp= confusion_matrix(y,yh,labels=[0,1]).ravel()
	fpr = fp / (fp +tn) if (fp +tn) else 0.0
	return dict(precision=p, recall=r, f1=f, fpr=fpr, accuracy =accuracy_score(y,yh))

def loco_rf(d, feats, seed=SEED):
	logo= LeaveOneGroupOut(); var= np.full(len(d), -1, int); g=d["cell"].values
	X= d[feats].values; y=d["label"].values
	for tr, te in logo.split(X,y,g):
		clf=RandomForestClassifier(n_estimators=NTREES, random_state=seed, n_jobs=1).fit(X[tr], y[tr])
		var[te]=clf.predict(X[te])
	return var

def main():
	df= pd.read_csv(CSV); y= df["label"].values
	print(f"[rf] {len(df)} windows, {int(y.sum())} attack, form{df.cell.nunique()} captures\n")
	var=loco_rf(df,MAIN); m=metrics(y, var)
	print("MAIN random forest fetaures are = (count+structural+semantic, leave-one-cpature-out):")
	print(f" P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} FPR={m['fpr']:.3f} Acc={m['accuracy']:.3f}\n")
	print("RQ3 abalations (2x2):")
	print(f" label-rev	legit-deuath-in-normal	P	R	F1	FPR	Acc")
	for lab_in in (False, True):
		for legit_in in (True, False):
			d=df if legit_in else df[(df.label ==1) | ((df.label ==0) & (df.n_deauth ==0))].reset_index(drop=True)
			feats= MAIN + (LABELREV if lab_in else [])
			yh= loco_rf(d, feats); mm=metrics(d["label"].values, yh)
			print(f"  {'yes' if lab_in else 'no ':9s} {'yes' if legit_in else 'no ':22s}  {mm['precision']:.3f}  {mm['recall']:.3f}  {mm['f1']:.3f}  {mm['fpr']:.3f}  {mm['accuracy']:.3f}")
	out= df[["cell", "rate", "load", "win", "label"]].copy(); out["pred_rf"]=var
	os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
	p= os.path.join(ROOT, "results", "rf_predictions.csv"); out.to_csv(p, index=False)
	print (f"\nout-of-fold predcitons --> {p}")


if __name__ == "__main__":
    main()
