"""Independent table-level replay; never fit models or publish subject records."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

RUNS = {
    'representation': 'repeated_connectome_20260907_locked5',
    'site_motion_increment': 'incremental_imaging_20260908_locked',
    'demographic_increment': 'demographic_increment_20260908_locked_v2',
}
MODELS = {
    'representation': ['motion_only_lr','site_only_lr','site_motion_lr','pearson_lr','pearson_adjusted_lr','pearson_mlp_ens','tangent_lr','tangent_adjusted_lr','tangent_mlp_ens'],
    'site_motion_increment': ['site_motion_lr','tangent_lr','tangent_mlp','fusion_tangent_lr','fusion_tangent_mlp'],
    'demographic_increment': ['site_motion_lr','demographic_lr','full_covariates_lr','fusion_tangent_lr','fusion_tangent_mlp'],
}
ALPHAS = [0., .25, .5, .75, 1.]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def validate_tables(cohort, splits, predictions, *, repeats=5, folds=3, models):
    """Validate IDs before any metric; table order is never assumed to align."""
    c,s,p=cohort,splits,predictions
    for table,cols in [(c,['subject_id','label','site']), (s,['subject_id','label','site','repeat','fold','role']), (p,['subject_id','y','site','repeat','fold','model','score'])]:
        require(set(cols)<=set(table),f'Missing columns: {set(cols)-set(table)}')
        require(not table[cols].isna().any().any(),'Missing required value')
    require(c.subject_id.is_unique,'Duplicate cohort subject')
    require(set(c.label)=={0,1},'Expected binary cohort labels')
    require(not s.duplicated(['repeat','fold','subject_id']).any(),'Subject occurs in multiple roles')
    require(not p.duplicated(['repeat','model','subject_id']).any(),'Duplicate test prediction')
    require(set(p.model)==set(models),'Model coverage mismatch')
    require(np.isfinite(p.score.to_numpy(dtype=float)).all(),'Non-finite score')
    require(set(s.role)=={'train','validation','test'},'Unexpected split role')
    keys={(r,f) for r in range(1,repeats+1) for f in range(1,folds+1)}
    require(set(zip(s.repeat,s.fold))==keys and set(zip(p.repeat,p.fold))==keys,'Missing/extra fold')
    require(len(p)==len(c)*repeats*len(models),'Prediction row count mismatch')
    indexed=c.set_index('subject_id');all_ids=set(c.subject_id)
    for table,label in [(s,'label'),(p,'y')]:
        require(set(table.subject_id)<=all_ids,'Unknown subject ID')
        expected=indexed.loc[table.subject_id]
        require(np.array_equal(table[label].to_numpy(),expected.label.to_numpy()),'Label does not match cohort')
        require(np.array_equal(table.site.astype(str).to_numpy(),expected.site.astype(str).to_numpy()),'Site does not match cohort')
    for (r,f),group in s.groupby(['repeat','fold']):
        require(set(group.subject_id)==all_ids,'Split does not cover cohort')
        for role in ['train','validation','test']:
            require(set(group.loc[group.role.eq(role),'label'])=={0,1},'Role lacks a label class')
        expected=set(group.loc[group.role.eq('test'),'subject_id'])
        test=p[p.repeat.eq(r)&p.fold.eq(f)]
        for model in models:
            require(set(test.loc[test.model.eq(model),'subject_id'])==expected,'Prediction IDs differ from test split')
    for _,group in s[s.role.eq('test')].groupby('repeat'):
        require(len(group)==len(c) and group.subject_id.is_unique,'Each subject must be tested once per repeat')
    return {'subjects':len(c),'repeats':repeats,'folds_per_repeat':folds,'models':len(models),'prediction_rows':len(p)}

def within_site_auc(group):
    terms=[]
    for _,g in group.groupby('site'):
        weight=int((g.y==1).sum()*(g.y==0).sum())
        if weight:terms.append((weight,roc_auc_score(g.y,g.score)))
    return sum(w*a for w,a in terms)/sum(w for w,_ in terms) if terms else np.nan

def aggregate(predictions):
    folds=pd.DataFrame([dict(repeat=r,fold=f,model=m,auc=roc_auc_score(g.y,g.score),within_site_auc=within_site_auc(g))
                        for (r,f,m),g in predictions.groupby(['repeat','fold','model'])])
    repeats=folds.groupby(['repeat','model'])[['auc','within_site_auc']].mean().reset_index()
    summary=repeats.groupby('model').agg(mean_auc=('auc','mean'),sd_repeat_auc=('auc','std'),min_repeat_auc=('auc','min'),max_repeat_auc=('auc','max'),mean_within_site_auc=('within_site_auc','mean')).reset_index()
    return folds,repeats,summary

def combine_scores(base,image,alpha,*,image_float32=False):
    # Original incremental MLP arrays were float32: scalar multiplication happened
    # before their addition to float64 LR probabilities. CSV reload is float64.
    image=np.asarray(image,dtype=np.float32 if image_float32 else np.float64)
    return (1-alpha)*np.asarray(base,dtype=np.float64)+alpha*image

def select_alpha(validation_y, validation_base, validation_image):
    values=[roc_auc_score(validation_y,(1-a)*validation_base+a*validation_image) for a in ALPHAS]
    return next(a for a,v in zip(ALPHAS,values) if v>=max(values)-1e-12),values

def compare_table(computed,saved,keys,mapping):
    require(not saved.duplicated(keys).any(),'Duplicate aggregate key')
    a=computed.set_index(keys).sort_index();b=saved.set_index(keys).sort_index()
    require(a.index.equals(b.index),'Aggregate key mismatch')
    maximum=0.
    for new,old in mapping.items():
        delta=np.abs(a[new].to_numpy()-b[old].to_numpy())
        require(np.isfinite(delta).all() and np.max(delta,initial=0)<1e-10,'Saved metric mismatch: '+old)
        maximum=max(maximum,float(np.max(delta,initial=0)))
    return maximum

def replay_release(release,out):
    release=Path(release).resolve();out=Path(out).resolve()
    require(not out.exists(),'Output already exists; choose a new directory')
    require(not out.is_relative_to(release),'Output cannot be inside frozen release')
    inventory=json.loads((release/'MANIFEST.json').read_text(encoding="utf-8"))
    expected={x['path']:x['sha256'] for x in inventory['files']};used={};tables={};report={};exports={}
    def read(relative):
        path=release/relative;key=path.relative_to(release).as_posix()
        require(key in expected,'File absent from frozen manifest: '+key)
        value=sha256(path);require(value==expected[key],'Frozen file hash mismatch: '+key);used[key]=value
        return pd.read_csv(path,dtype={'subject_id':str})
    for stage,run in RUNS.items():
        prefix='runs/'+run+'/'
        c=read(prefix+'cohort.csv');s=read(prefix+'splits.csv');p=read(prefix+'predictions.csv')
        require(len(c)==378,'Unexpected frozen cohort size')
        item=validate_tables(c,s,p,models=MODELS[stage]);fm,rm,sm=aggregate(p)
        saved=read(prefix+'fold_metrics.csv');mapping={k:k for k in ['auc','within_site_auc'] if k in saved}
        item['max_fold_auc_error']=compare_table(fm,saved,['repeat','fold','model'],mapping)
        saved_summary=read(prefix+'summary.csv')
        mapping={'mean_auc':'mean','sd_repeat_auc':'std','min_repeat_auc':'min','max_repeat_auc':'max'} if stage=='representation' else ({'mean_auc':'mean_auc','min_repeat_auc':'min_auc','max_repeat_auc':'max_auc','mean_within_site_auc':'within_site_auc'} if stage=='demographic_increment' else {k:k for k in sm if k!='model'})
        item['max_summary_error']=compare_table(sm,saved_summary,['model'],mapping)
        report[stage]=item;tables[stage]=(c,s,p);exports[stage]=(fm,rm,sm)
    # Same cohort, labels, and role assignment across all three analyses.
    c0,s0,_=tables['representation']
    for c,s,_ in tables.values():
        for a,b,keys,cols in [(c,c0,['subject_id'],['label','site']),(s,s0,['repeat','fold','subject_id'],['label','site','role'])]:
            require(a.set_index(keys)[cols].sort_index().equals(b.set_index(keys)[cols].sort_index()),'Analysis cohort/splits changed')
    selections=[]
    for stage in ['site_motion_increment','demographic_increment']:
        _,splits,p=tables[stage];prefix='runs/'+RUNS[stage]+'/'
        saved=read(prefix+'selection.csv');require(len(saved)==150,'Unexpected alpha-search table size')
        for (r,f),test in p.groupby(['repeat','fold']):
            inc=read('runs/'+RUNS['site_motion_increment']+f'/repeat{r}_fold{f}_validation.csv')
            val=inc if stage=='site_motion_increment' else read(prefix+f'repeat{r}_fold{f}/validation.csv')
            ids=splits[splits.repeat.eq(r)&splits.fold.eq(f)&splits.role.eq('validation')].subject_id.tolist()
            labels=c0.set_index('subject_id').loc[ids,'label'].to_numpy()
            for v in [inc,val]:
                require(not v.duplicated(['subject_id','model']).any(),'Duplicate validation prediction')
                for _,g in v.groupby('model'):
                    require(set(g.subject_id)==set(ids),'Validation membership mismatch')
                    require(np.array_equal(g.set_index('subject_id').loc[ids,'y'],labels),'Validation label mismatch')
                require(np.isfinite(v.score).all(),'Nonfinite validation score')
            vi=inc.pivot(index='subject_id',columns='model',values='score').loc[ids]
            vb=val.pivot(index='subject_id',columns='model',values='score').loc[ids]
            bt='site_motion_lr' if stage=='site_motion_increment' else 'full_covariates_lr'
            tw=test.pivot(index='subject_id',columns='model',values='score')
            image_test=tables['site_motion_increment'][2]
            image_test=image_test[image_test.repeat.eq(r)&image_test.fold.eq(f)].pivot(index='subject_id',columns='model',values='score').loc[tw.index]
            for model in ['tangent_lr','tangent_mlp']:
                image_float32=stage=='site_motion_increment' and model=='tangent_mlp'
                image_val=vi[model].to_numpy(dtype=np.float32 if image_float32 else np.float64)
                a,values=select_alpha(labels,vb[bt].to_numpy(),image_val)
                g=saved[saved.repeat.eq(r)&saved.fold.eq(f)&saved.image_model.eq(model)].sort_values('alpha')
                require(len(g)==5 and g.alpha.tolist()==ALPHAS,'Alpha grid mismatch')
                require(g.selected.isin([True,False]).all() and g.selected.sum()==1,'Invalid selected-alpha flags')
                require(float(g.loc[g.selected,'alpha'].iloc[0])==a,'Selected alpha mismatch')
                np.testing.assert_allclose(g.validation_auc,values,rtol=0,atol=1e-10)
                np.testing.assert_allclose(tw['fusion_'+model],combine_scores(tw[bt],image_test[model],a,image_float32=image_float32),rtol=0,atol=1e-10)
                np.testing.assert_allclose(vb['fusion_'+model],combine_scores(vb[bt],vi[model],a,image_float32=image_float32),rtol=0,atol=1e-10)
                selections.append(dict(stage=stage,repeat=int(r),fold=int(f),image_model=model,alpha=a))
    # No output is created until every evidence check has passed.
    out.mkdir(parents=True)
    for stage,(fm,rm,sm) in exports.items():
        for name,frame in [('fold_metrics',fm),('repeat_metrics',rm),('summary',sm)]:frame.to_csv(out/(stage+'_'+name+'.csv'),index=False)
    pd.DataFrame(selections).to_csv(out/'selected_alphas.csv',index=False)
    pairs=[]
    for stage,a,b in [('representation','tangent_lr','pearson_lr'),('representation','tangent_mlp_ens','pearson_mlp_ens'),('representation','tangent_mlp_ens','tangent_lr'),('demographic_increment','fusion_tangent_mlp','full_covariates_lr'),('demographic_increment','fusion_tangent_lr','full_covariates_lr')]:
        w=exports[stage][1].pivot(index='repeat',columns='model',values='auc');delta=w[a]-w[b]
        pairs.append(dict(stage=stage,candidate=a,reference=b,mean_delta=delta.mean(),min_delta=delta.min(),max_delta=delta.max(),positive_repeats=int((delta>1e-12).sum()),repeats=5))
    pd.DataFrame(pairs).to_csv(out/'paired_deltas.csv',index=False)
    report={'status':'passed','scope':'Frozen file integrity, subject/role/label membership, fold and summary AUC, validation alpha selection and score-fusion arithmetic. Not raw preprocessing reconstruction or full model refitting.', 'runs':report,'validation_alpha_checks':len(selections),'source_sha256':used,'limitations':'Internal reused cohort. Repeat ranges/SD are not confidence intervals; scores are not calibrated clinical risks.'}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report
