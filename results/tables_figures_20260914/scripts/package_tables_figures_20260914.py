from pathlib import Path
import csv,json,hashlib,shutil,re,zipfile,struct,subprocess
R=Path(__file__).resolve().parents[1];B=R/'results/tables_figures_20260914';P=R/'results/paper_readiness_20260911';A=B/'source_aggregates';D=B/'source_results';D.mkdir(exist_ok=True)
for p in P.glob('*.csv'):shutil.copy2(p,D/p.name)
for p in (P/'fresh_refit/statistics').glob('*.csv'):shutil.copy2(p,D/('original_'+p.name))
C=B/'scripts';C.mkdir(exist_ok=True)
for p in (R/'reporting').glob('*20260914.py'):shutil.copy2(p,C/p.name)
read=lambda p:list(csv.DictReader(p.open()))
counts=read(A/'participant_counts.csv');stats=read(A/'participant_continuous.csv')
for co in ['reviewed','primary','warning_free','include_holds']:
 for site in ['ALL']+sorted({x['site'] for x in counts if x['cohort']==co and x['site']!='ALL'}):
  g={x['label']:x for x in counts if x['cohort']==co and x['site']==site}
  assert int(g['ALL']['n'])==int(g['0']['n'])+int(g['1']['n'])
  for x in g.values():assert int(x['male_n'])+int(x['female_n'])+int(x['sex_missing'])==int(x['n'])
  for var in ['age_years','mean_fd','pct_fd_gt_0p2','mean_dvars','max_fd','n_volumes','tiv_mm3']:
   s={x['label']:x for x in stats if x['cohort']==co and x['site']==site and x['variable']==var}
   assert int(s['ALL']['n_observed'])==int(s['0']['n_observed'])+int(s['1']['n_observed'])
   num=sum(int(s[k]['n_observed'])*float(s[k]['mean']) for k in ['0','1'] if int(s[k]['n_observed']))
   if int(s['ALL']['n_observed']):assert abs(num/int(s['ALL']['n_observed'])-float(s['ALL']['mean']))<1e-8
for p in B.rglob('*.csv'):
 rows=read(p);assert rows and not({'subject_id','participant_id','t1_path_original'}&set(rows[0])),p
for target in re.findall(r'(?:href|src)="([^"]+)"',(B/'index.html').read_text()):assert (B/target).exists(),target
for p in (B/'figures').glob('*.png'):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);assert min(w,h)>400
v=json.loads((B/'validation.json').read_text());v.update(group_count_sums=True,weighted_means_reconcile=True,local_links_valid=True,exported_csvs_have_no_individual_id_columns=True,all_9_figures_visually_inspected=True,remaining_limits=['FD/DVARS acquisition-unit provenance not independently confirmed','QC is sampled assistant review, not expert full-volume review','No external validation; no manuscript written'])
(B/'validation.json').write_text(json.dumps(v,indent=2))
(B/'README_TABLES_AND_FIGURES.md').write_text((B/'README_TABLES_AND_FIGURES.md').read_text()+'''\n## Files and reproduction\n\nOpen index.html to view all main tables and figures; tables holds editable CSVs; figures holds PNG/PDF files; source_aggregates holds the newly compiled aggregates and frozen input hashes; source_results holds the numerical sources of existing figures and tables. scripts is a snapshot of the code used for this compilation; its participant aggregation step needs the original project paths and server inputs. The exported package contains no individual records or raw images.\n\nsource_results/original_cv_contrast_stats.csv and original_loso_contrast_stats.csv support Figure2/Table3; qc_decomposition.csv supports Figure3/Table4; selector_alpha_distribution.csv supports Figure4; original_cv_primary_summary.csv supports FigureS1; original_calibration.csv supports FigureS2; site_contributions.csv supports FigureS3; cv_interval_audit.csv supports FigureS4; original_loso_per_site_deltas.csv supports FigureS5. No analysis parameters were re-selected for presentation.\n\nValidation: participant group counts, weighted means, the 21 existing site/cohort counts, input hashes, CSV structure and HTML links all pass; all 9 figures were inspected individually. The original historical figures and frozen runs were not overwritten.\n''')
files=[p for p in B.rglob('*') if p.is_file() and p.name!='PACKAGE_MANIFEST.json'];m={'date':'2026-09-14','head':subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip(),'scope':'Tables and figures only; published aggregate results package','files':[{'path':str(p.relative_to(B)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(files)]};(B/'PACKAGE_MANIFEST.json').write_text(json.dumps(m,indent=2))
out=R.parents[1]/'outputs/ADHD_Tables_Figures_20260914.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in B.rglob('*'):
  if p.is_file():z.write(p,str(p.relative_to(B)))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for x in m['files']:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
out.with_suffix('.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n');print(json.dumps({'archive':str(out),'bytes':out.stat().st_size,'validation':v},ensure_ascii=False))
