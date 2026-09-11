"""Fresh v2 fitting from frozen time series/volumes; no original run writes.

Uses the hash-identical legacy training implementation in a new environment.
Recomputes within-person covariance and all training-only transforms from scratch.
This is independent execution, not an independently authored model implementation.
"""
from pathlib import Path
import argparse, concurrent.futures, contextlib, importlib.metadata, json, multiprocessing, os, re, shutil, sys, time, traceback
import numpy as np
import pandas as pd
from integrity import digest, verify_manifest, compare_predictions

HERE=Path(__file__).resolve().parent
LEGACY=HERE/'legacy'
COHORTS=['primary','warning_free','include_holds']
SITES=['KKI','NYU','NeuroIMAGE','OHSU','Peking_1','Peking_2','Peking_3']


def write_json(p,obj):
    temp=p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n');temp.replace(p)


def import_training():
    sys.path.insert(0,str(LEGACY))
    import run_structural_fusion_v2 as train
    return train


def jobs():
    return [(fw,co,tag) for fw in ['cv','loso'] for co in COHORTS for tag in
            ([f'repeat{r}_fold{f}' for r in range(1,6) for f in range(1,4)] if fw=='cv' else ['site_'+s for s in SITES])]


def unit(source,out,job):
    import torch
    from threadpoolctl import threadpool_limits
    train=import_training();train.OUT=out
    fw,co,tag=job;old=source/'runs/structural_fusion_v2_20260910'/fw/co/tag;dest=out/fw/co/tag
    if (dest/'comparison.json').exists():
        m=json.loads((dest/'complete.json').read_text());verify_manifest(dest,m['files'])
        return json.loads((dest/'comparison.json').read_text())
    if dest.exists() and any(dest.iterdir()):raise RuntimeError(f'incomplete unit requires explicit isolated retry: {fw}/{co}/{tag}')
    dest.mkdir(parents=True,exist_ok=True)
    with (dest/'reproduction.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        started=time.monotonic();torch.set_num_threads(4)
        c=pd.read_csv(out/fw/co/'cohort.csv');sp=pd.read_csv(out/fw/co/'splits.csv');lookup={s:i for i,s in enumerate(c.subject_id)}
        expected=json.loads((old/'audit.json').read_text())
        if fw=='cv':
            r,f=map(int,re.fullmatch(r'repeat(\d+)_fold(\d+)',tag).groups());g=sp[sp.repeat.eq(r)&sp.fold.eq(f)]
            tr,va,te=[np.array([lookup[s] for s in g[g.role.eq(role)].subject_id]) for role in ['train','validation','test']]
            fold_id=f;seed_off=f*10+r
        else:
            site=tag[5:];si=SITES.index(site);ss=c.site.astype(str).to_numpy();te=np.where(ss==site)[0]
            tr,va=train.inner_holdout(c,np.where(ss!=site)[0],si);fold_id=si+1;seed_off=si
        for k,ix in [('train_ids',tr),('validation_ids',va),('test_ids',te)]:
            if c.subject_id.iloc[ix].tolist()!=expected[k]:raise ValueError(f'frozen role mismatch {tag}/{k}')
        z=np.load(source/'runs/structural_features378_20260909/volumes_NOT_TRAINING_READY.npz',allow_pickle=False)
        vi={s:i for i,s in enumerate(z['subject_id'].astype(str))};ix=[vi[s] for s in c.subject_id]
        vol=z['volume_fractions'][ix];tiv=z['total_intracranial_mm3'][ix];z.close()
        meta=json.loads((out/'covariances.json').read_text());ci={s:i for i,s in enumerate(meta['ids'])}
        cov0=np.load(out/'covariances.npy',mmap_mode='r');cov=np.asarray(cov0[[ci[s] for s in c.subject_id]])
        with threadpool_limits(limits=4):train.run_fold(c,vol,tiv,cov,tr,va,te,fold_id,seed_off,dest)
        comparisons={}
        for role in ['validation','test']:
            a=pd.read_csv(old/(role+'.csv'));b=pd.read_csv(dest/(role+'.csv'))
            if set(a.model)!=set(train.MODEL_NAMES) or set(b.model)!=set(train.MODEL_NAMES):raise ValueError('model set mismatch')
            comparisons[role]=compare_predictions(a,b)
        selections_a=pd.read_csv(old/'selection.csv');selections_b=pd.read_csv(dest/'selection.csv')
        sa=selections_a[selections_a.selected.astype(str).str.lower().eq('true')][['model','alpha']].sort_values('model').reset_index(drop=True)
        sb=selections_b[selections_b.selected.astype(str).str.lower().eq('true')][['model','alpha']].sort_values('model').reset_index(drop=True)
        result=dict(framework=fw,cohort=co,unit=tag,seconds=time.monotonic()-started,predictions=comparisons,
                    fusion_weights_identical=sa.equals(sb),fresh_fit=True,geometry_recomputed_from_scratch=True)
        write_json(dest/'comparison.json',result)
        # Training's marker includes the live log, which continues growing. Rebuild our separate output manifest after closing it.
    marker=json.loads((dest/'complete.json').read_text())
    marker['files']={p.name:digest(p) for p in dest.iterdir() if p.is_file() and p.name!='complete.json'}
    write_json(dest/'complete.json',marker)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--workers',type=int,default=4);ap.add_argument('--limit',type=int);ap.add_argument('--prepare-only',action='store_true')
    args=ap.parse_args();source=args.source.resolve();out=args.out.resolve();original=source/'runs/structural_fusion_v2_20260910'
    if out==original or original in out.parents:raise ValueError('output must be independent of original run')
    train=import_training();proto=json.loads((original/'protocol_v2.json').read_text())
    verify_manifest(source,proto['input_hashes']);verify_manifest(LEGACY,proto['code_hashes'])
    verify_manifest(LEGACY,json.loads((HERE/'legacy_manifest.json').read_text()))
    import torch
    from threadpoolctl import threadpool_limits
    torch.set_num_threads(4)
    for job in jobs():
        folder=original.joinpath(*job);m=json.loads((folder/'complete.json').read_text())
        if m['protocol_sha256']!=digest(original/'protocol_v2.json'):raise ValueError('original unit protocol mismatch')
        verify_manifest(folder,m['files'])
    out.mkdir(parents=True,exist_ok=True)
    package_names=['numpy','pandas','scipy','scikit-learn','torch','joblib','threadpoolctl']
    manifest=dict(original_protocol_sha256=digest(original/'protocol_v2.json'),legacy_manifest_sha256=digest(HERE/'legacy_manifest.json'),
                  runner_sha256=digest(Path(__file__)),integrity_sha256=digest(HERE/'integrity.py'),
                  python=sys.version,packages={n:importlib.metadata.version(n) for n in package_names},
                  original_input_hashes=proto['input_hashes'],planned_units=66,threads_per_worker=4,
                  scope='Fresh covariance, training geometry, preprocessing, model fitting, validation selection and predictions from frozen A424 time series and regional volumes; not raw MRI preprocessing.')
    mp=out/'reproduction_manifest.json'
    if mp.exists() and json.loads(mp.read_text())!=manifest:raise ValueError('reproduction source/environment changed')
    write_json(mp,manifest)
    (out/'protocol_v2.json').write_bytes((original/'protocol_v2.json').read_bytes())
    for fw in ['cv','loso']:
        for co in COHORTS:
            d=out/fw/co;d.mkdir(parents=True,exist_ok=True)
            for name in ['cohort.csv','splits.csv']:(d/name).write_bytes((original/fw/co/name).read_bytes())
    train.OUT=out;train.CACHE=source/'runs/temporal_cache_20260907_113751'
    c0=pd.read_csv(source/'runs/demographic_increment_20260908_locked_v2/cohort.csv')
    with threadpool_limits(limits=4):fresh=train.covariance_cache(c0)
    saved=np.load(original/'covariances.npy',mmap_mode='r')
    maxdiff=float(np.max(np.abs(fresh-saved)));np.testing.assert_allclose(fresh,saved,rtol=1e-12,atol=1e-12)
    write_json(out/'covariance_comparison.json',dict(max_abs_difference=maxdiff,sha256_identical=digest(out/'covariances.npy')==digest(original/'covariances.npy'),recomputed_from_timeseries=True))
    del fresh,saved
    if args.prepare_only:return
    todo=jobs()[:args.limit] if args.limit else jobs();results=[]
    started=time.monotonic();write_json(out/'reproduction_status.json',dict(status='running',planned=len(todo),completed=0,pid=os.getpid()))
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            futures={pool.submit(unit,source,out,job):job for job in todo}
            for future in concurrent.futures.as_completed(futures):
                result=future.result();results.append(result)
                write_json(out/'reproduction_status.json',dict(status='running',planned=len(todo),completed=len(results),last_unit=list(futures[future]),seconds=time.monotonic()-started,pid=os.getpid()))
                print('COMPLETE',len(results),'/',len(todo),'/'.join(futures[future]),round(result['seconds'],1),flush=True)
        allmatch=all(r['fusion_weights_identical'] and all(p['scores_match_rtol_1e_5_atol_1e_6'] for p in r['predictions'].values()) for r in results)
        report=dict(status='complete_matched' if allmatch else 'complete_with_differences',units=len(results),planned=66,
                    all_units_completed=len(results)==66,all_predictions_within_tolerance=allmatch,results=results,seconds=time.monotonic()-started)
        write_json(out/'reproduction_report.json',report);write_json(out/'reproduction_status.json',{k:v for k,v in report.items() if k!='results'})
        if len(results)==66:
            train.OUT=out;train.summarize_cv();train.summarize_loso()
        print('FINAL',report['status'],len(results),flush=True)
    except BaseException as e:
        write_json(out/'reproduction_status.json',dict(status='failed',completed=len(results),error=repr(e)));raise

if __name__=='__main__':main()
