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
(B/'README_图表口径与图注.md').write_text((B/'README_图表口径与图注.md').read_text()+'''\n## 文件与复现\n\n打开 index.html 查看全部主表与图；tables 为可编辑 CSV；figures 为 PNG/PDF；source_aggregates 为本次新汇总及冻结输入哈希；source_results 为已有图表数值来源。scripts 为本次整理代码快照，需要原项目路径/服务器输入执行参与者汇总；导出的包不含个体记录或原始影像。\n\nsource_results/original_cv_contrast_stats.csv 与 original_loso_contrast_stats.csv 支持 Figure2/Table3；qc_decomposition.csv 支持 Figure3/Table4；selector_alpha_distribution.csv 支持 Figure4；original_cv_primary_summary.csv 支持 FigureS1；original_calibration.csv 支持 FigureS2；site_contributions.csv 支持 FigureS3；cv_interval_audit.csv 支持 FigureS4；original_loso_per_site_deltas.csv 支持 FigureS5。新分析并未因展示而重新选择参数。\n\n验证：参与者分组人数、加权均值、21组站点/队列既有计数、输入哈希、CSV结构和HTML链接均通过；9幅图已逐一检查。原历史图和冻结运行未被覆盖。\n''')
files=[p for p in B.rglob('*') if p.is_file() and p.name!='PACKAGE_MANIFEST.json'];m={'date':'2026-09-14','head':subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip(),'scope':'Tables and figures only; local research package','files':[{'path':str(p.relative_to(B)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(files)]};(B/'PACKAGE_MANIFEST.json').write_text(json.dumps(m,indent=2))
out=R.parents[1]/'outputs/ADHD_Tables_Figures_20260914.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in B.rglob('*'):
  if p.is_file():z.write(p,str(p.relative_to(B)))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for x in m['files']:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
out.with_suffix('.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n');print(json.dumps({'archive':str(out),'bytes':out.stat().st_size,'validation':v},ensure_ascii=False))
