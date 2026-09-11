"""Conditional final-alpha stability from validation-only resampling.
Fixed fitted models and the upstream functional fusion; no refitting, no test selection.
"""
from pathlib import Path
import argparse,hashlib
import numpy as np
import pandas as pd
from statistics_audit import COHORTS,CAND,REF,paired_scores,auc,select_alpha


def resampled_choices(w,n_boot,seed):
    grid=np.array([0.,.25,.5,.75,1.]);y=w.y.to_numpy();base=w.reference.to_numpy();added=w.candidate.to_numpy()
    pos=np.flatnonzero(y==1);neg=np.flatnonzero(y==0);rng=np.random.default_rng(seed)
    counts=np.zeros((n_boot,len(w)),dtype=int)
    for _,g in w.reset_index(drop=True).groupby(['site','y']):
        ix=g.index.to_numpy();counts[:,ix]=rng.multinomial(len(ix),np.full(len(ix),1/len(ix)),size=n_boot)
    vals=[]
    for a in grid:
        s=(1-a)*base+a*added;matrix=(s[pos,None]>s[neg]).astype(float)+.5*(s[pos,None]==s[neg])
        vals.append(np.einsum('bi,ij,bj->b',counts[:,pos],matrix,counts[:,neg],optimize=True)/(len(pos)*len(neg)))
    vals=np.asarray(vals);chosen=np.argmax(vals>=vals.max(axis=0)-1e-12,axis=0)
    return grid[chosen]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[];hist=[]
    for fw in ['cv','loso']:
        for co in COHORTS:
            for folder in sorted((a.run/fw/co).glob('*')):
                if not (folder/'validation.csv').exists():continue
                p=pd.read_csv(folder/'validation.csv',dtype={'subject_id':str});v=paired_scores(p,'structural_mlp',REF)
                sel=pd.read_csv(folder/'selection.csv');original=float(sel[sel.model.eq(CAND)&sel.selected.astype(str).str.lower().eq('true')].iloc[0].alpha)
                actual=select_alpha(v.y.to_numpy(),v.reference.to_numpy(),v.candidate.to_numpy())
                if actual!=original:raise ValueError(f'original alpha not reconstructed: {folder.name}')
                seed=20260911+int(hashlib.sha256(f'{fw}/{co}/{folder.name}'.encode()).hexdigest()[:6],16)
                draws=resampled_choices(v,1000,seed)
                pp=pd.read_csv(folder/'test.csv',dtype={'subject_id':str});t=paired_scores(pp,'structural_mlp',REF)
                grid=[0.,.25,.5,.75,1.]
                deltas={alpha:auc(t.y,(1-alpha)*t.reference+alpha*t.candidate)-auc(t.y,t.reference) for alpha in grid}
                evaluated=np.array([deltas[x] for x in draws])
                rows.append(dict(framework=fw,cohort=co,unit=folder.name,validation_n=len(v),original_alpha=original,
                                 probability_same_alpha=float(np.mean(draws==original)),probability_zero_alpha=float(np.mean(draws==0)),
                                 original_test_delta=deltas[original],conditional_test_delta_q05=float(np.quantile(evaluated,.05)),
                                 conditional_test_delta_q95=float(np.quantile(evaluated,.95)),
                                 bootstrap_repetitions=1000,scope='fixed_models_final_alpha_only_validation_site_label_bootstrap'))
                for alpha in grid:hist.append(dict(framework=fw,cohort=co,unit=folder.name,alpha=alpha,probability=float(np.mean(draws==alpha))))
    pd.DataFrame(rows).to_csv(a.out/'selector_stability.csv',index=False)
    pd.DataFrame(hist).to_csv(a.out/'selector_alpha_distribution.csv',index=False)
    d=pd.DataFrame(rows);print(d[d.framework.eq('loso')&d.unit.eq('site_NYU')].to_string(index=False))

if __name__=='__main__':main()
