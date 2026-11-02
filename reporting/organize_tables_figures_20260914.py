from pathlib import Path
import csv,json,hashlib,shutil,html,zipfile
R=Path(__file__).resolve().parents[1];B=R/'results/tables_figures_20260914';A=B/'source_aggregates';P=R/'results/paper_readiness_20260911';S=P/'fresh_refit/statistics';T=B/'tables';F=B/'figures';T.mkdir(exist_ok=True);F.mkdir(exist_ok=True)
def read(p):return list(csv.DictReader(p.open()))
def save(name,rows):
 with (T/(name+'.csv')).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 return rows
counts=read(A/'participant_counts.csv');stats=read(A/'participant_continuous.csv')
def count(co,site,label):return next(x for x in counts if (x['cohort'],x['site'],x['label'])==(co,site,label))
def stat(co,site,label,var):return next(x for x in stats if (x['cohort'],x['site'],x['label'],x['variable'])==(co,site,label,var))
def summary(co,site,label,var,mode='median',scale=1,dec=2):
 x=stat(co,site,label,var)
 if not int(x['n_observed']):return 'NA'
 keys=['mean','sd'] if mode=='mean' else ['median','q1','q3'];v=[f'{float(x[k])*scale:.{dec}f}' for k in keys];s=f'{v[0]} ({v[1]})' if mode=='mean' else f'{v[0]} [{v[1]}, {v[2]}]'
 return s+f"; missing {x['n_missing']}"
def group_table(co,site='ALL'):
 rows=[]
 def add(name,fn):rows.append({'Characteristic':name,**{label:fn(k) for k,label in [('ALL','All'),('0','Control (label 0)'),('1','ADHD (label 1)')]}})
 add('Participants, n',lambda k:count(co,site,k)['n'])
 for col,title in [('male_n','Recorded male sex, n (%)'),('female_n','Recorded female sex, n (%)')]:
  add(title,lambda k,col=col: f"{count(co,site,k)[col]} ({100*int(count(co,site,k)[col])/int(count(co,site,k)['n']):.1f}%)" if int(count(co,site,k)['n']) else 'NA')
 add('Age (years), mean (SD)',lambda k:summary(co,site,k,'age_years','mean'))
 add('Age (years), median [Q1, Q3]',lambda k:summary(co,site,k,'age_years'))
 add('Mean FD (metadata scale), median [Q1, Q3]',lambda k:summary(co,site,k,'mean_fd',dec=3))
 add('Frames with FD > 0.2 (%), median [Q1, Q3]',lambda k:summary(co,site,k,'pct_fd_gt_0p2',scale=100,dec=1))
 add('Mean DVARS (metadata scale), median [Q1, Q3]',lambda k:summary(co,site,k,'mean_dvars',dec=3))
 add('TIV (mL), mean (SD)',lambda k:summary(co,site,k,'tiv_mm3','mean',scale=.001,dec=1))
 if site=='ALL':
  for s in sorted({x['site'] for x in counts if x['cohort']==co and x['site']!='ALL'}):add(s+', n (%)',lambda k,s=s:f"{count(co,s,k)['n']} ({100*int(count(co,s,k)['n'])/int(count(co,'ALL',k)['n']):.1f}%)")
 return rows
main1=save('Table1_primary_participants',group_table('primary'))
sup=[]
for co in ['primary','warning_free','include_holds']:
 for site in ['ALL']+sorted({x['site'] for x in counts if x['cohort']==co and x['site']!='ALL'}):
  sup += [{'Cohort':co,'Site':site,**x} for x in group_table(co,site)]
save('TableS1_participants_by_cohort_site_diagnosis',sup)
cv={x['model']:x for x in read(S/'cv_primary_summary.csv')};lo={x['model']:x for x in read(S/'loso_primary_summary.csv')}
models=['full_covariates_lr','structural_lr','structural_mlp','tangent_lr','tangent_mlp','full_functional_mlp','full_fusion_structural_mlp']
perf=[{'Model':m,'CV mean fold AUC':f"{float(cv[m]['mean_auc']):.4f}",'LOSO within-site pair-weighted AUC':f"{float(lo[m]['pair_weighted_auc']):.4f}",'LOSO equal-site macro AUC':f"{float(lo[m]['macro_auc']):.4f}"} for m in models];save('Table2_primary_model_performance',perf)
save('TableS2_all_17_primary_outputs',[{'Model':m,**{('CV '+k):v for k,v in cv[m].items() if k!='model'},**{('LOSO '+k):v for k,v in lo[m].items() if k!='model'}} for m in cv])
contr=[]
for fw,file,metric,key,method in [('CV','cv_contrast_stats.csv','auc','mean_delta','Original corrected t interval; df=14'),('LOSO','loso_contrast_stats.csv','pair_weighted','point','Original within-site subject bootstrap; 10000 draws')]:
 for x in read(S/file):
  if x['contrast']=='P' and x['metric']==metric:contr.append({'Framework':fw,'Cohort':x['cohort'],'Delta AUC':f"{float(x[key]):+.4f}",'90% interval':f"[{float(x['ci90_lo']):+.4f}, {float(x['ci90_hi']):+.4f}]",'Uncertainty method':method})
save('Table3_primary_contrast_by_QC',contr)
for new,src in [('Table4_QC_decomposition',P/'qc_decomposition.csv'),('TableS3_final_alpha_decomposition',P/'fusion_decomposition_summary.csv'),('TableS4_missingness',A/'missingness.csv'),('TableS5_analysis_role_counts',A/'analysis_role_counts.csv'),('TableS6_QC_counts_by_site_label',A/'qc_flow.csv'),('TableS7_CV_interval_sensitivity',P/'cv_interval_audit.csv'),('TableS8_LOSO_bootstrap_sensitivity',P/'loso_summaries.csv'),('TableS9_selector_stability',P/'selector_stability.csv'),('TableS10_calibration',S/'calibration_summary.csv')]:shutil.copy2(src,T/(new+'.csv'))
figmap=[('Figure3_QC_decomposition',R/'figures/paper_readiness_20260911/F1_qc_decomposition'),('Figure4_NYU_selector_stability',R/'figures/paper_readiness_20260911/F4_NYU_selector_stability'),('FigureS2_calibration',S/'figures/v2_F3_reliability'),('FigureS3_site_contributions',R/'figures/paper_readiness_20260911/F2_site_contributions'),('FigureS4_CV_interval_sensitivity',R/'figures/paper_readiness_20260911/F3_cv_interval_sensitivity')]
for name,src in figmap:
 for ext in ['.png','.pdf']:
  if src.with_suffix(ext).exists():shutil.copy2(src.with_suffix(ext),F/(name+ext))
captions={
'Figure1_participant_flow':'QC flow starting from the verified paired cohort of 378 participants. Three failed image quality; the remaining 375 form the include-HOLD cohort. Excluding 25 HOLD cases gives the primary cohort of 350; excluding a further 48 signal warnings gives the warning-free cohort of 302. The three cohorts overlap. QC was a sampled assisted review, not an expert full-volume assessment. Earlier recruitment and screening steps are not reconstructed in this figure.',
'Figure2_primary_contrast':'Primary contrast: full_fusion_structural_mlp − full_functional_mlp. CV shows the mean of the 15 fold differences with the original corrected-t 90% interval; LOSO shows the within-site case–control pair-weighted ΔAUC with the original 90% interval from 10,000 within-site subject bootstrap draws. The grey band marks ±0.02. The two intervals rest on different conditions; the LOSO interval does not include uncertainty from retraining or from sampling new sites.',
'Figure3_QC_decomposition':'Post hoc decomposition of the change across QC cohorts. Using common test participants and fixed primary-cohort site weights, it separates the contributions of the fitting pipeline, the evaluated sample composition and the site weights. The components reconstruct the total difference exactly; this is a descriptive decomposition, not a causal effect.',
'Figure4_NYU_selector_stability':'Selection stability of the final structural fusion weight for the NYU held-out fold, from 1,000 bootstrap draws by site and label within the internal validation sets of the remaining training sites only; fitted models, upstream weights and early stopping were held fixed. This is not tuning on NYU test data and not a whole-pipeline confidence interval.',
'FigureS1_CV_models':'The seven primary-cohort models shown by fixed research role, matching Table2. Points are mean fold AUC; error bars span the minimum to the maximum of the five repeat means and are not confidence intervals. All 17 outputs are listed in TableS2.',
'FigureS2_calibration':'Descriptive calibration curves for the frozen repeated-CV predictions. The primary-cohort n=1750 means five predictions for each of 350 participants, not 1,750 independent participants. Weighted training outputs are not validated individual diagnostic risks.',
'FigureS3_site_contributions':'Site contributions to the pair-weighted result. NYU accounts for 39.7% of primary-cohort participants but 67.07% of the within-site positive–negative pair weight; its primary-cohort structural increment is zero, so the overall positive increment cannot be attributed to NYU.',
'FigureS4_CV_interval_sensitivity':'Post hoc interval sensitivity to the degrees-of-freedom and test/fit-ratio conventions. All intervals come from the same set of results; they are not independent replications.',
'FigureS5_LOSO_contrasts':'Estimates of the primary structural increment by site and QC cohort; error bars are the original 95% within-site subject bootstrap intervals, which differ from the overall 90% intervals in Figure2. Intervals are conditional on the observed sites and frozen models; small-site estimates are imprecise, and the executed LOSO did not refit on all training sites after selection.'}
notes='''# Tables and figures — 2026-09-14\n\nPurpose: this document collects the definitions behind the tables and the figure captions, as a reference for manuscript writing and result checking. ADHD-200 data use terms are in the repository's docs/DATA.md. This page is not manuscript text, is not for clinical diagnosis, and involves no new model training.\n\n## Table definitions\n\n- Table1: primary cohort, grouped by the frozen binary label; mean (sample SD) or median [Q1, Q3]. Continuous values are observed values before imputation, with the number missing listed alongside; the denominator for categorical percentages is the column total.\n- Age and sex use the actual model inputs participant_age / participant_sex_male. This is recorded sex, not gender identity. Following the project mapping, label 1 is called ADHD and label 0 control; clinical diagnoses were not independently re-reviewed.\n- Head-motion pct_fd_gt_0p2 is stored as a 0–1 proportion and shown as a percentage (×100); TIV is converted from mm³ to mL (÷1000). FD/DVARS keep their metadata scale; their acquisition and computation units must be confirmed before formal submission. No participants were removed as outliers.\n- Table2: CV is the mean fold AUC, aggregated over repeats; it is not an AUC computed on all repeated predictions pooled together. LOSO pair-weighted and equal-site macro averages are listed separately and are not interchangeable. The seven displayed models are fixed by research role; the full table of 17 outputs is TableS2 and was not filtered by score.\n- Table3: the primary contrast with its original intervals; TableS7/S8 are interval sensitivity analyses added later and are not the same bootstrap.\n- Table4/TableS3: post hoc descriptive decompositions. All QC cohorts overlap; no independent between-group tests were run.\n- TableS5: training/validation/test counts listed for the 66 units; their sum cannot be read as a number of participants.\n\n## Method boundaries\n\nLOSO used a single 85/15 split within the six training sites and did not refit on all six sites after selection. The current results reflect this pipeline as executed. Full reproduction starts only from the frozen time series and volume derivatives; raw MRI preprocessing, complete expert QC and external validation are not established by it.\n\n## Figure captions\n\n'''+''.join(f'### {k}\n\n{v}\n\n' for k,v in captions.items())
(B/'README_TABLES_AND_FIGURES.md').write_text(notes)
style='body{font:16px system-ui,sans-serif;color:#183044;margin:32px auto;max-width:1180px;line-height:1.6}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:8px;border-bottom:1px solid #dce4ea;text-align:left}th{background:#edf3f7;position:sticky;top:0}figure{margin:36px 0}img{max-width:100%}section{margin:32px 0}.scroll{overflow:auto}a{color:#126998}small{color:#526574}@media print{section,figure{break-inside:avoid}th{position:static}}'
def table(rows):
 keys=list(rows[0]);return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in keys)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x[k]))+'</td>' for k in keys)+'</tr>' for x in rows)+'</tbody></table></div>'
body='<h1>ADHD: Tables & Figures</h1><p>2026-09-14 · for research analysis · compiled from frozen results</p><p>4 main tables + 10 supplementary tables; 4 main figures + 5 supplementary figures. CSVs are editable; figures can be downloaded as PNG, with PDF where a vector version exists.</p><p><strong>Table 1 definitions:</strong> continuous variables are summarized before imputation; missing is the number of participants missing. Percentage denominators are the column counts. The three QC cohorts overlap. The head-motion threshold proportion is shown as a percentage, and TIV has been converted from mm³ to mL.</p><p><a href="README_TABLES_AND_FIGURES.md">Statistical definitions, captions and limitations</a></p>'
for name,title in [('Table1_primary_participants','Table 1. Primary-cohort participant characteristics'),('Table2_primary_model_performance','Table 2. Model performance in the primary cohort'),('Table3_primary_contrast_by_QC','Table 3. Primary contrast across QC cohorts'),('Table4_QC_decomposition','Table 4. Descriptive decomposition of QC changes')]:
 body+='<section><h2>'+title+'</h2><a href="tables/'+name+'.csv">Download CSV</a>'+table(read(T/(name+'.csv')))+'</section>'
for name,caption in captions.items():
 if (F/(name+'.png')).exists():body+='<figure><h2>'+name+'</h2><a href="figures/'+name+'.png"><img src="figures/'+name+'.png"></a><figcaption>'+caption+'</figcaption>'+('<a href="figures/'+name+'.pdf">PDF</a>' if (F/(name+'.pdf')).exists() else '')+'</figure>'
body+='<h2>Supplementary tables</h2><ul>'+''.join('<li><a href="tables/'+p.name+'">'+p.stem+'</a></li>' for p in sorted(T.glob('TableS*.csv')) )+'</ul>'
(B/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ADHD Tables & Figures</title><style>'+style+'</style>'+body+'</html>')
# Verify source counts against prior released aggregate table.
for x in read(P/'cohort_site_counts.csv'):
 c=count(x['cohort'],x['site'],'ALL');assert int(c['n'])==int(x['n']) and int(c['label1_n'])==int(x['adhd']) and int(c['label0_n'])==int(x['control'])
validation={'unique_subject_counts_match_prior_21_site_cohort_rows':True,'source_manifest_hashes_match':all(hashlib.sha256((A/n).read_bytes()).hexdigest()==h for n,h in json.loads((A/'participant_aggregation_manifest.json').read_text())['files'].items()),'table_count':len(list(T.glob('*.csv'))),'figure_png_count':len(list(F.glob('*.png'))),'new_training':False,'manuscript_written':False}
(B/'validation.json').write_text(json.dumps(validation,indent=2));print(json.dumps(validation))
