"""Post hoc audit; preserves the original v2 decision and reports distinct estimands."""
from pathlib import Path
import argparse, hashlib, itertools, json
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score

COHORTS=['primary','warning_free','include_holds']
CAND='full_fusion_structural_mlp'
REF='full_functional_mlp'


def auc(y,score):
    y=np.asarray(y)
    return float(roc_auc_score(y,score)) if len(np.unique(y))==2 else float('nan')


def paired_scores(p,candidate,reference):
    cols=['subject_id','site','y','score']
    a=p.loc[p.model.eq(candidate),cols].copy()
    b=p.loc[p.model.eq(reference),cols].copy()
    if a.subject_id.duplicated().any() or b.subject_id.duplicated().any():
        raise ValueError('duplicate subject keys within model/evaluation unit')
    if set(a.subject_id)!=set(b.subject_id) or a.empty:
        raise ValueError('subject keys must match exactly')
    a=a.set_index('subject_id').sort_index();b=b.set_index('subject_id').loc[a.index]
    if not np.array_equal(a.y,b.y):raise ValueError('label mismatch')
    if not np.array_equal(a.site,b.site):raise ValueError('site mismatch')
    if not np.isfinite(a.score).all() or not np.isfinite(b.score).all():raise ValueError('nonfinite scores')
    return a[['site','y']].assign(candidate=a.score,reference=b.score).reset_index()


def interval_evidence(lo,hi,margin=.02):
    if not np.isfinite([lo,hi]).all() or lo>hi:raise ValueError('invalid interval')
    return dict(equivalence_supported=bool(lo>=-margin and hi<=margin),
                positive_supported=bool(lo>0),negative_supported=bool(hi<0),
                meaningful_positive_supported=bool(lo>margin),meaningful_negative_supported=bool(hi< -margin),
                meaningful_positive_excluded=bool(hi<margin),meaningful_negative_excluded=bool(lo> -margin))


def decompose_shift(full_a,full_b,common_a,common_b):
    total=full_b-full_a
    model=common_b-common_a
    composition=(full_b-common_b)-(full_a-common_a)
    return dict(total_shift=total,common_subject_model_shift=model,evaluation_composition_shift=composition,
                identity_residual=total-model-composition)


def shapley_two_factor(aa,ab,ba,bb):
    prediction=.5*((ba-aa)+(bb-ab))
    weight=.5*((ab-aa)+(bb-ba))
    return dict(prediction_contribution=prediction,fusion_weight_contribution=weight,
                identity_residual=(bb-aa)-prediction-weight)


def select_alpha(y,base,added):
    grid=[0.,.25,.5,.75,1.]
    values=[auc(y,(1-a)*base+a*added) for a in grid]
    return next(a for a,v in zip(grid,values) if v>=max(values)-1e-12)


def by_site(w):
    rows=[]
    for s,g in w.groupby('site',sort=True):
        pos=int(g.y.sum());neg=len(g)-pos
        rows.append(dict(site=s,n=len(g),pos=pos,neg=neg,pairs=pos*neg,
                         candidate_auc=auc(g.y,g.candidate),reference_auc=auc(g.y,g.reference),
                         delta=auc(g.y,g.candidate)-auc(g.y,g.reference)))
    return pd.DataFrame(rows).set_index('site')


def weighted_delta(s,weights=None):
    if weights is None:weights=s.pairs
    weights=weights.reindex(s.index)
    if weights.isna().any() or not np.isfinite(s.delta).all() or (weights<0).any() or weights.sum()<=0:
        raise ValueError('unestimable site or missing fixed weight')
    return float(np.dot(weights/weights.sum(),s.delta))


def conditional_boot(w,weights,n_boot=2000,seed=20260911):
    # Site and outcome counts fixed. This is conditional inference, not uncertainty over new sites or fits.
    rng=np.random.default_rng(seed)
    gs=[g for _,g in w.groupby('site',sort=True)]
    ww=weights.reindex([g.site.iloc[0] for g in gs]).to_numpy(float,copy=True);ww/=ww.sum()
    vals=np.zeros(n_boot)
    for weight,g in zip(ww,gs):
        y=g.y.to_numpy();a=g.candidate.to_numpy();b=g.reference.to_numpy()
        i0=np.flatnonzero(y==0);i1=np.flatnonzero(y==1)
        if not len(i0) or not len(i1):raise ValueError('single-class site')
        # Pair-indicator matrices correctly give half credit to cross-class ties.
        diff=(a[i1,None]>a[i0]).astype(float)+.5*(a[i1,None]==a[i0])
        diff-=(b[i1,None]>b[i0]).astype(float)+.5*(b[i1,None]==b[i0])
        c0=rng.multinomial(len(i0),np.full(len(i0),1/len(i0)),size=n_boot)
        c1=rng.multinomial(len(i1),np.full(len(i1),1/len(i1)),size=n_boot)
        vals+=weight*np.einsum('bi,ij,bj->b',c1,diff,c0,optimize=True)/(len(i0)*len(i1))
    return np.quantile(vals,[.05,.95]).tolist()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    fingerprints={}; wide={};sites={};counts=[];summary=[];influence=[];contrib=[];decomps=[];decomp_sites=[];cvrows=[];alphas=[]
    for co in COHORTS:
        pth=a.run/'loso'/co/'predictions.csv';fingerprints[str(pth.relative_to(a.run))]=hashlib.sha256(pth.read_bytes()).hexdigest()
        p=pd.read_csv(pth,dtype={'subject_id':str});w=paired_scores(p,CAND,REF);wide[co]=w;sites[co]=by_site(w)
        s=sites[co]
        for site,row in s.iterrows():counts.append(dict(cohort=co,site=site,n=int(row.n),adhd=int(row.pos),control=int(row.neg)))
    weights=sites['primary'].pairs
    for co in COHORTS:
        w=wide[co];s=sites[co]
        if set(s.index)!=set(weights.index):raise ValueError('site sets differ')
        native=s.pairs/s.pairs.sum();fixed=weights/weights.sum();macro=pd.Series(1/len(s),index=s.index)
        for metric,wt in [('native_pair_weighted',native),('fixed_primary_site_weights',fixed),('macro',macro)]:
            point=weighted_delta(s,wt);lo,hi=conditional_boot(w,wt)
            summary.append(dict(cohort=co,metric=metric,delta=point,ci90_lo=lo,ci90_hi=hi,
                                uncertainty='conditional_site_and_class_stratified_subject_bootstrap_2000',**interval_evidence(lo,hi)))
            for dropped in s.index:
                keep=s.index[s.index!=dropped];estimate=weighted_delta(s.loc[keep],wt.loc[keep])
                influence.append(dict(cohort=co,metric=metric,excluded_site=dropped,full_delta=point,delta_without_site=estimate,change=estimate-point,scope='aggregation_only_no_refit'))
        for site,row in s.iterrows():
            contrib.append(dict(cohort=co,site=site,site_delta=row.delta,native_weight=native.loc[site],fixed_weight=fixed.loc[site],
                                native_contribution=native.loc[site]*row.delta,fixed_contribution=fixed.loc[site]*row.delta))
    for ca,cb in itertools.combinations(COHORTS,2):
        wa,wb=wide[ca],wide[cb];ids=set(wa.subject_id)&set(wb.subject_id)
        aa=wa[wa.subject_id.isin(ids)].sort_values('subject_id');bb=wb[wb.subject_id.isin(ids)].sort_values('subject_id')
        if not np.array_equal(aa[['subject_id','site','y']].to_numpy(),bb[['subject_id','site','y']].to_numpy()):raise ValueError('cross-cohort identity mismatch')
        sa,sb=by_site(aa),by_site(bb)
        if set(sa.index)!=set(weights.index):raise ValueError('common cohort loses site')
        native_a=weighted_delta(sites[ca]);native_b=weighted_delta(sites[cb])
        full_a=weighted_delta(sites[ca],weights);full_b=weighted_delta(sites[cb],weights)
        common_a=weighted_delta(sa,weights);common_b=weighted_delta(sb,weights)
        d=decompose_shift(full_a,full_b,common_a,common_b)
        weight_shift=(native_b-full_b)-(native_a-full_a)
        residual=(native_b-native_a)-(weight_shift+d['common_subject_model_shift']+d['evaluation_composition_shift'])
        if abs(residual)>1e-12:raise ValueError('decomposition identity failed')
        decomps.append(dict(cohort_a=ca,cohort_b=cb,common_n=len(ids),native_a=native_a,native_b=native_b,
                            common_fixed_a=common_a,common_fixed_b=common_b,weight_shift=weight_shift,
                            total_native_shift=native_b-native_a,**d,three_component_residual=residual))
        for site in sa.index:
            dd=decompose_shift(sites[ca].loc[site,'delta'],sites[cb].loc[site,'delta'],sa.loc[site,'delta'],sb.loc[site,'delta'])
            decomp_sites.append(dict(cohort_a=ca,cohort_b=cb,site=site,common_n=int(sa.loc[site,'n']),**dd))
    for co in COHORTS:
        fm=pd.read_csv(a.run/'cv'/co/'fold_metrics.csv')
        fwide=fm.pivot(index=['repeat','fold'],columns='model',values='auc');d=(fwide[CAND]-fwide[REF]).to_numpy()
        split=pd.read_csv(a.run/'cv'/co/'splits.csv');sz=split.groupby(['repeat','fold','role']).size().unstack()
        # Original correction uses outer train+validation as training size. Additional sensitivity uses actual fit rows.
        ratios={'original_outer_train_plus_validation':.5,'actual_fit_rows_sensitivity':float((sz['test']/sz['train']).mean())}
        for ratio_tag,ratio in ratios.items():
            se=np.sqrt((1/len(d)+ratio)*d.var(ddof=1))
            for df in [14,2]:
                lo,hi=d.mean()+np.array([-1,1])*stats.t.ppf(.95,df)*se
                cvrows.append(dict(cohort=co,contrast='P',ratio_definition=ratio_tag,test_train_ratio=ratio,df=df,mean_delta=d.mean(),ci90_lo=lo,ci90_hi=hi,**interval_evidence(lo,hi)))
        for fw in ['cv','loso']:
            for pth in sorted((a.run/fw/co).glob('*/selection.csv')):
                sel=pd.read_csv(pth);sel=sel[(sel.model==CAND)&sel.selected.astype(str).str.lower().eq('true')]
                if len(sel)!=1:raise ValueError('missing/duplicate selected primary fusion weight')
                alphas.append(dict(framework=fw,cohort=co,unit=pth.parent.name,alpha=float(sel.iloc[0].alpha)))
    tables={'cohort_site_counts':counts,'loso_summaries':summary,'site_influence':influence,'site_contributions':contrib,
            'qc_decomposition':decomps,'qc_decomposition_per_site':decomp_sites,'cv_interval_audit':cvrows,'selected_primary_weights':alphas}
    for name,rows in tables.items():pd.DataFrame(rows).to_csv(a.out/(name+'.csv'),index=False)
    original=json.loads((a.run/'v2_stats/decision.json').read_text())
    report=dict(analysis='post_hoc_paper_readiness',source_prediction_sha256=fingerprints,original_v2_decision=original,
                primary_hypothesis_confirmed=False,causal_attribution=False,
                interpretation='No equivalence confirmation. Primary LOSO positive interval does not establish delta > .02. QC sensitivity does not invalidate LOSO or prove absence of leakage.',
                decomposition='Exact descriptive identity at fixed primary site weights. Common-subject model difference includes training composition, tuning, and stochastic trajectories; not isolated biological effect.',
                bootstrap_scope='Sites and class counts fixed, existing predictions; excludes training and unseen-site uncertainty. Different bootstrap target from original site-only resampling.',
                nb_scope='Approximate corrected CV inference; actual-fit ratio is disclosed sensitivity, not a replacement preregistered estimator.',
                max_decomposition_residual=max(abs(r['three_component_residual']) for r in decomps))
    (a.out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(pd.DataFrame(decomps).to_string(index=False));print('OUTPUT',a.out)

if __name__=='__main__':main()
