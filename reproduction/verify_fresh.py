"""Independent completion gate for the preserved September 11 execution.

Preflight is read-only. Final mode must run after fitting exits and regenerates
statistics in a new separate directory. Nothing in the original run is written.
"""
from pathlib import Path
import argparse,json,sys,subprocess,importlib.metadata
import numpy as np
import pandas as pd
from integrity import digest,verify_manifest,compare_predictions
from completion import write_json,publish_unit,verify_unit

HERE=Path(__file__).resolve().parent
COHORTS=['primary','warning_free','include_holds']
SITES=['KKI','NYU','NeuroIMAGE','OHSU','Peking_1','Peking_2','Peking_3']


def jobs():
    return [(fw,co,tag) for fw in ['cv','loso'] for co in COHORTS for tag in
            ([f'repeat{r}_fold{f}' for r in range(1,6) for f in range(1,4)] if fw=='cv' else ['site_'+s for s in SITES])]


def preflight(source,out):
    original=source/'runs/structural_fusion_v2_20260910'
    proto=json.loads((original/'protocol_v2.json').read_text())
    verify_manifest(source,proto['input_hashes'])
    reference=json.loads((HERE/'reference_manifest.json').read_text())['files']
    verify_manifest(original,reference)
    verify_manifest(HERE/'legacy',json.loads((HERE/'legacy_manifest.json').read_text()))
    verify_manifest(HERE/'legacy',proto['code_hashes'])
    cache=source/'runs/temporal_cache_20260907_113751'
    ts_hash=json.loads((cache/'verification.json').read_text())['cache_sha256']
    if digest(cache/'timeseries.npz')!=ts_hash:raise ValueError('time-series checksum mismatch')
    manifest=json.loads((out/'reproduction_manifest.json').read_text())
    allowed={digest(HERE/'reproduce_v2.py'),digest(HERE/'execution_history/reproduce_v2_launched_20260911.py')}
    if manifest['runner_sha256'] not in allowed:raise ValueError('unrecognized execution source')
    if manifest['integrity_sha256']!=digest(HERE/'integrity.py'):raise ValueError('execution comparator changed')
    if manifest['legacy_manifest_sha256']!=digest(HERE/'legacy_manifest.json'):raise ValueError('legacy changed')
    if manifest['original_protocol_sha256']!=digest(original/'protocol_v2.json'):raise ValueError('protocol changed')
    if digest(out/'protocol_v2.json')!=digest(original/'protocol_v2.json'):raise ValueError('copied protocol changed')
    for fw in ['cv','loso']:
        for co in COHORTS:
            for name in ['cohort.csv','splits.csv']:
                if digest(out/fw/co/name)!=reference[f'{fw}/{co}/{name}']:raise ValueError('fitting metadata changed')
    fresh_meta=json.loads((out/'covariances.json').read_text())
    old_meta=json.loads((original/'covariances.json').read_text())
    if fresh_meta['ids']!=old_meta['ids'] or fresh_meta['source_sha256']!=ts_hash:raise ValueError('covariance provenance changed')
    if digest(out/'covariances.npy')!=fresh_meta['sha256']:raise ValueError('covariance artifact changed')
    if digest(out/'covariances.npy')!=digest(original/'covariances.npy'):raise ValueError('covariance differs')
    for job in jobs():
        d=original.joinpath(*job);m=json.loads((d/'complete.json').read_text())
        if m['protocol_sha256']!=digest(original/'protocol_v2.json'):raise ValueError('original completion protocol mismatch')
        verify_manifest(d,m['files'])
    return dict(status='preflight_verified',reference_snapshot_files=len(reference),metadata_files=12,
                timeseries_sha256=ts_hash,covariance_sha256=digest(out/'covariances.npy'),
                execution_runner_sha256=manifest['runner_sha256'],verifier_sha256=digest(Path(__file__)),
                reference_manifest_sha256=digest(HERE/'reference_manifest.json'))


def validate_units(source,out):
    original=source/'runs/structural_fusion_v2_20260910';checks=[]
    for fw,co,tag in jobs():
        old=original/fw/co/tag;new=out/fw/co/tag
        # Legacy execution is accepted here only after global completion, with every
        # finalized artifact verified and all comparisons independently recomputed.
        marker=json.loads((new/'complete.json').read_text());verify_manifest(new,marker['files'])
        if marker['protocol_sha256']!=digest(original/'protocol_v2.json'):raise ValueError('fresh unit protocol changed')
        audit_old=json.loads((old/'audit.json').read_text());audit_new=json.loads((new/'audit.json').read_text())
        for role in ['train_ids','validation_ids','test_ids']:
            if audit_old[role]!=audit_new[role]:raise ValueError('fresh role identities changed')
        rows={}
        for role in ['validation','test']:
            a=pd.read_csv(old/(role+'.csv'));b=pd.read_csv(new/(role+'.csv'))
            if a.model.nunique()!=17 or set(a.model)!=set(b.model):raise ValueError('model coverage differs')
            rows[role]=compare_predictions(a,b)
            if not rows[role]['scores_match_rtol_1e_5_atol_1e_6']:raise ValueError('prediction tolerance exceeded')
        selected=[]
        for d in [old,new]:
            s=pd.read_csv(d/'selection.csv');selected.append(s[s.selected.astype(str).str.lower().eq('true')][['model','alpha']].sort_values('model').reset_index(drop=True))
        pd.testing.assert_frame_equal(*selected,check_exact=True)
        stored=json.loads((new/'comparison.json').read_text())
        if stored['predictions']!=rows or not stored['fusion_weights_identical']:raise ValueError('stored comparison disagrees')
        if tuple(stored[k] for k in ['framework','cohort','unit'])!=(fw,co,tag):raise ValueError('stored job identity differs')
        publish_unit(new);verify_unit(new,expected_job=(fw,co,tag),protocol_hash=digest(original/'protocol_v2.json'))
        checks.append(dict(framework=fw,cohort=co,unit=tag,predictions=rows,fusion_weights_identical=True))
    return checks


def validate_summaries(source,out):
    original=source/'runs/structural_fusion_v2_20260910';checks=[]
    for fw in ['cv','loso']:
        status=json.loads((out/fw/'status.json').read_text())
        if status['status']!='complete_replay_checked':raise ValueError('framework summary incomplete')
        for co in COHORTS:
            d=out/fw/co;parts=[]
            for jf,jc,tag in jobs():
                if (jf,jc)!=(fw,co):continue
                p=pd.read_csv(d/tag/'test.csv')
                if fw=='cv':
                    r,f=tag.removeprefix('repeat').split('_fold');p=p.assign(repeat=int(r),fold=int(f))
                parts.append(p)
            expected=pd.concat(parts,ignore_index=True);actual=pd.read_csv(d/'predictions.csv')
            pd.testing.assert_frame_equal(expected,actual,check_exact=False,rtol=1e-14,atol=1e-15)
            names=['summary.csv','fold_metrics.csv','repeat_metrics.csv'] if fw=='cv' else ['summary.csv','site_metrics.csv']
            for name in names:
                a=pd.read_csv(original/fw/co/name);b=pd.read_csv(d/name)
                pd.testing.assert_frame_equal(a,b,check_exact=False,rtol=1e-10,atol=1e-12)
                checks.append(dict(framework=fw,cohort=co,file=name,rows=len(b),matched=True))
    return checks


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--preflight',action='store_true');ap.add_argument('--stats-out',type=Path)
    a=ap.parse_args();source=a.source.resolve();out=a.out.resolve()
    original=source/'runs/structural_fusion_v2_20260910'
    if out==original or original in out.parents:raise ValueError('refuse original output path')
    if a.preflight:print(json.dumps(preflight(source,out),indent=2));return
    terminal=out/'verified_reproduction.json';terminal.unlink(missing_ok=True)
    try:
        if a.stats_out is None:raise ValueError('--stats-out must be a new independent directory')
        stats_out=a.stats_out.resolve()
        if stats_out==source or source in stats_out.parents:raise ValueError('statistics output must be outside original source workspace')
        if stats_out.exists():raise ValueError('statistics output must be a new directory')
        evidence=preflight(source,out)
        status=json.loads((out/'reproduction_status.json').read_text())
        if status.get('status')!='complete_matched' or not status.get('all_units_completed') or status.get('units')!=66:
            raise ValueError('fitting has not completed and matched all 66 units')
        checks=validate_units(source,out);summaries=validate_summaries(source,out)
        subprocess.run([sys.executable,str(HERE/'regenerate_tables.py'),'--run',str(out),'--reference-run',str(original),'--out',str(a.stats_out.resolve())],check=True)
        stats=json.loads((a.stats_out/'recomputation_verification.json').read_text())
        # Recheck immutable source inputs after the complete validation chain.
        if preflight(source,out)!=evidence:raise ValueError('source changed during verification')
        final=dict(status='verified_full_feature_level_reproduction',all_units_completed=True,units=66,models_per_unit=17,
                   evidence=evidence,unit_comparisons=checks,summary_comparisons=summaries,statistics=stats,
                   audit_environment=dict(python=sys.version,packages={n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','matplotlib']}),
                   scope='Fresh fitting from frozen time-series/volume derivatives; not raw MRI preprocessing or external validation.')
        write_json(terminal,final)
        write_json(out/'verification_status.json',dict(status=final['status'],units=66))
        print('VERIFIED FULL FEATURE-LEVEL REPRODUCTION: 66/66 units; tables, decision and figures verified.',flush=True)
    except BaseException as exc:
        terminal.unlink(missing_ok=True)
        write_json(out/'verification_status.json',dict(status='failed',error=repr(exc)))
        raise

if __name__=='__main__':main()
