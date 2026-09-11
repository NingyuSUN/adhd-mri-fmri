"""Post hoc symmetric decomposition of model and selected-alpha contributions.
Cross-applied weights are descriptive counterfactual evaluations, never model selection.
"""
from pathlib import Path
import argparse,itertools,json
import numpy as np
import pandas as pd
from statistics_audit import COHORTS,CAND,REF,auc,paired_scores,by_site,shapley_two_factor


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    data={};weights={};rows=[];summ=[]
    for co in COHORTS:
        p=pd.read_csv(a.run/'loso'/co/'predictions.csv',dtype={'subject_id':str})
        x=paired_scores(p,'structural_mlp',REF).rename(columns={'candidate':'structure','reference':'functional'})
        saved=paired_scores(p,CAND,REF).set_index('subject_id')
        for site,g in x.groupby('site'):
            sel=pd.read_csv(a.run/'loso'/co/('site_'+site)/'selection.csv')
            chosen=sel[sel.model.eq(CAND)&sel.selected.astype(str).str.lower().eq('true')]
            if len(chosen)!=1:raise ValueError('selected alpha missing')
            alpha=float(chosen.iloc[0].alpha);weights[co,site]=alpha
            pred=(1-alpha)*g.functional.to_numpy()+alpha*g.structure.to_numpy()
            np.testing.assert_allclose(pred,saved.loc[g.subject_id].candidate.to_numpy(),rtol=1e-6,atol=1e-7)
        data[co]=x.set_index('subject_id')
    primary=data['primary'];pairweights=primary.groupby('site').y.agg(lambda y:y.sum()*(len(y)-y.sum()));pairweights/=pairweights.sum()
    for ca,cb in itertools.combinations(COHORTS,2):
        common=data[ca].index.intersection(data[cb].index).sort_values();aa=data[ca].loc[common];bb=data[cb].loc[common]
        if not np.array_equal(aa[['site','y']],bb[['site','y']]):raise ValueError('cross-cohort subject metadata mismatch')
        parts=[]
        for site in sorted(aa.site.unique()):
            ga=aa[aa.site.eq(site)];gb=bb.loc[ga.index];alpa=weights[ca,site];alpb=weights[cb,site]
            def delta(g,alpha):return auc(g.y,(1-alpha)*g.functional+alpha*g.structure)-auc(g.y,g.functional)
            da=delta(ga,alpa);dab=delta(ga,alpb);dba=delta(gb,alpa);db=delta(gb,alpb)
            d=shapley_two_factor(da,dab,dba,db)
            r=dict(cohort_a=ca,cohort_b=cb,site=site,common_n=len(ga),alpha_a=alpa,alpha_b=alpb,
                   delta_model_a_alpha_a=da,delta_model_a_alpha_b=dab,delta_model_b_alpha_a=dba,delta_model_b_alpha_b=db,
                   common_model_shift=db-da,primary_site_weight=float(pairweights[site]),**d)
            if abs(d['identity_residual'])>1e-12:raise ValueError('two-factor identity failed')
            rows.append(r);parts.append(r)
        summ.append(dict(cohort_a=ca,cohort_b=cb,
                         common_model_shift=sum(r['primary_site_weight']*r['common_model_shift'] for r in parts),
                         prediction_contribution=sum(r['primary_site_weight']*r['prediction_contribution'] for r in parts),
                         fusion_weight_contribution=sum(r['primary_site_weight']*r['fusion_weight_contribution'] for r in parts)))
    pd.DataFrame(rows).to_csv(a.out/'fusion_decomposition_per_site.csv',index=False)
    pd.DataFrame(summ).to_csv(a.out/'fusion_decomposition_summary.csv',index=False)
    print(pd.DataFrame(summ).to_string(index=False))

if __name__=='__main__':main()
