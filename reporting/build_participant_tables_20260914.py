"""Aggregate frozen participant metadata only; does not fit models or export records."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import pandas as pd

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();b=a.source;o=a.out;o.mkdir(parents=True,exist_ok=False)
 run=b/'runs/structural_fusion_v2_20260910';proto=json.loads((run/'protocol_v2.json').read_text())
 for rel,h in proto['input_hashes'].items():assert sha(b/rel)==h,rel
 parent=b/'runs/demographic_increment_20260908_locked_v2/cohort.csv';qcpath=b/'runs/structural_qc_locked_20260909/qc_lock.json';c=pd.read_csv(parent,dtype={'subject_id':str});q=json.loads(qcpath.read_text());qs=pd.DataFrame(q['subjects']);assert len(c)==378 and c.subject_id.is_unique
 assert set(c.subject_id)==set(qs.subject_id);assert not c[['label_conflict','age_conflict','sex_conflict']].any().any();assert set(c.label)=={0,1};assert c.participant_sex_male.dropna().isin([0,1]).all()
 c=c.merge(qs[['subject_id','qc_status','total_intracranial_mm3']],on='subject_id',validate='one_to_one')
 cols={'age_years':'participant_age','mean_fd':'mean_fd','pct_fd_gt_0p2':'pct_fd_gt_0p2','mean_dvars':'mean_dvars','max_fd':'max_fd','n_volumes':'n_volumes','tiv_mm3':'total_intracranial_mm3'}
 stats=[];counts=[];missing=[];roles=[];sources={str(parent.relative_to(b)):sha(parent),str(qcpath.relative_to(b)):sha(qcpath)}
 for co in ['reviewed','primary','warning_free','include_holds']:
  cc=c if co=='reviewed' else c[c.subject_id.isin(q['cohorts'][co])]
  if co!='reviewed':
   for fw in ['cv','loso']:
    cp=run/fw/co/'cohort.csv';saved=pd.read_csv(cp,dtype={'subject_id':str});assert set(saved.subject_id)==set(cc.subject_id);sources[str(cp.relative_to(b))]=sha(cp)
    for unit in (run/fw/co).iterdir():
     if not unit.is_dir() or not (unit/'audit.json').exists():continue
     aud=json.loads((unit/'audit.json').read_text())
     for role in ['train','validation','test']:
      rr=cc[cc.subject_id.isin(aud[role+'_ids'])];assert len(rr)==len(aud[role+'_ids'])
      roles.append(dict(framework=fw,cohort=co,unit=unit.name,role=role,n=len(rr),label1=int(rr.label.sum()),label0=int((rr.label==0).sum())))
  for site in ['ALL']+sorted(cc.site.unique()):
   ss=cc if site=='ALL' else cc[cc.site.eq(site)]
   for label in ['ALL',0,1]:
    g=ss if label=='ALL' else ss[ss.label.eq(label)]
    sex=g.participant_sex_male
    counts.append(dict(cohort=co,site=site,label=str(label),n=len(g),male_n=int(sex.eq(1).sum()),female_n=int(sex.eq(0).sum()),sex_missing=int(sex.isna().sum()),label1_n=int(g.label.eq(1).sum()),label0_n=int(g.label.eq(0).sum())))
    for key,col in cols.items():
     raw=pd.to_numeric(g[col],errors='raise');v=raw[np.isfinite(raw)]
     stats.append(dict(cohort=co,site=site,label=str(label),variable=key,n_total=len(g),n_observed=len(v),n_missing=len(g)-len(v),mean=float(v.mean()) if len(v) else None,sd=float(v.std(ddof=1)) if len(v)>1 else None,median=float(v.median()) if len(v) else None,q1=float(v.quantile(.25)) if len(v) else None,q3=float(v.quantile(.75)) if len(v) else None,min=float(v.min()) if len(v) else None,max=float(v.max()) if len(v) else None))
   for col in list(cols.values())+['participant_sex_male','label']:
    raw=pd.to_numeric(ss[col],errors='raise');missing.append(dict(cohort=co,site=site,variable=col,n_total=len(ss),n_missing=int((~np.isfinite(raw)).sum())))
 tables={'participant_counts':pd.DataFrame(counts),'participant_continuous':pd.DataFrame(stats),'missingness':pd.DataFrame(missing),'analysis_role_counts':pd.DataFrame(roles),'qc_flow':c.groupby(['site','qc_status','label']).size().rename('n').reset_index()}
 for name,t in tables.items():t.to_csv(o/(name+'.csv'),index=False)
 role=tables['analysis_role_counts'];assert len(role)==198
 checks={'parent_n':len(c),'cohort_n':{co:len(q['cohorts'][co]) for co in ['primary','warning_free','include_holds']},'qc_counts':c.qc_status.value_counts().to_dict(),'units':len(role)//3,'no_conflicting_labels_age_sex':True,'cohort_membership_matches_cv_and_loso':True,'only_aggregates_exported':True}
 assert checks['cohort_n']=={'primary':350,'warning_free':302,'include_holds':375}
 for rel,h in sources.items():assert sha(b/rel)==h
 manifest={'source_root':str(b),'sources':sources,'checks':checks,'definition':{'label':'Frozen binary label 1 versus 0; clinical ascertainment not independently re-reviewed','age':'participant_age, as consumed by demographic()','sex':'participant_sex_male (1 male, 0 female); not gender identity','missing':'Raw pre-imputation non-finite values','sd':'Sample SD, ddof=1','quantiles':'pandas default linear interpolation','grouping':'Unique subjects; cohorts overlap; no group-comparison p values'},'files':{p.name:sha(p) for p in o.glob('*.csv')}}
 (o/'participant_aggregation_manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False));print(json.dumps(checks))
if __name__=='__main__':main()
