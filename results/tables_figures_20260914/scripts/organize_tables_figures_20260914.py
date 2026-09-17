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
'Figure1_participant_flow':'从已核实的 378 人配对队列开始的 QC 流程。3 人影像质量失败；其余 375 人构成含 HOLD 队列。再排除 25 个 HOLD 得到主队列 350 人；再排除 48 个信号警告得到无警告队列 302 人。三个队列重叠。QC 为抽样辅助审查，不等于专家全体积判定。更早的数据招募/筛选流程未在本图重建。',
'Figure2_primary_contrast':'主要比较：full_fusion_structural_mlp − full_functional_mlp。CV 为 15 折差值的均值及原始修正 t 90% 区间；LOSO 为站点内病例–对照配对加权 ΔAUC 及原始 10,000 次站点内受试者 bootstrap 90% 区间。灰带为 ±0.02。两类区间的条件不同；LOSO 不包含重新训练或新站点抽样的不确定性。',
'Figure3_QC_decomposition':'事后分解 QC 队列变化。共同测试参与者与固定主队列站点权重下，分解拟合流程、评估样本组成和站点权重贡献。分量精确重构总差，属于描述性分解，不是因果效应。',
'Figure4_NYU_selector_stability':'NYU 留出折最终结构融合权重的选择稳定性。只在其余训练站点的内部验证集中，按站点和标签 bootstrap 1,000 次；拟合模型、上游权重和早停保持固定。不是 NYU 测试数据选参，也不是全流程置信区间。',
'FigureS1_CV_models':'主队列 7 个按研究角色固定展示的模型，与 Table2 一致。点为平均折 AUC；误差条为5次重复均值的最小值至最大值，不是置信区间。17 个输出完整数值见 TableS2。',
'FigureS2_calibration':'冻结重复 CV 预测的描述性校准曲线。主队列 n=1750 指 350 人各 5 次预测；不是 1750 位独立参与者。加权训练输出不是已验证的个体诊断风险。',
'FigureS3_site_contributions':'站点对配对加权结果的贡献。NYU 占主队列人数 39.7%，占站点内正负配对权重 67.07%；其主队列结构增量为零，不能把总体正增量归因于 NYU。',
'FigureS4_CV_interval_sensitivity':'对自由度与 test/fit 比例约定的事后区间敏感性。各区间来自同一批结果，不是独立重复研究。',
'FigureS5_LOSO_contrasts':'主要结构增量在各站点和 QC 队列的估计，误差条为原始95%站点内受试者 bootstrap 区间。不同于 Figure2 的总体90%区间。区间条件于已观察站点及冻结模型；小站点估计不精确，实际LOSO没有选择后全训练站点重拟合。'}
notes='''# Tables and figures — 2026-09-14\n\n用途：本文档汇总图表口径与图注，供论文写作与结果核查参考。ADHD-200 数据使用条款见 DATA.md；本页不构成论文正文，不用于临床诊断，也不涉及新的模型训练。\n\n## 表格口径\n\n- Table1：主队列，按冻结二分类标签分组；均值（样本 SD）或中位数 [Q1,Q3]。连续值为填补前观测值，并列缺失人数；类别百分比分母为相应列总人数。\n- 年龄/性别采用实际模型输入 participant_age / participant_sex_male。这里是记录的 sex，不等于 gender identity。标签1按项目映射称 ADHD，标签0称对照，未独立重审临床诊断。\n- 头动 pct_fd_gt_0p2 原值为 0–1 比例，显示为百分比乘100；TIV 从 mm³ 转 mL 除1000。FD/DVARS 保留元数据量纲，采集与计算来源单位需在正式投稿前核实。没有按异常值重新删人。\n- Table2：CV 是平均折 AUC，经重复汇总；不是将所有重复预测混合后算的 AUC。LOSO 配对加权与等站点宏平均分别列出，不互换。7 个展示模型按研究角色固定；17 个输出全表在 TableS2，未按高分筛选。\n- Table3：主比较及原始区间；TableS7/S8 为后来增加的区间敏感性，不能混为同一种 bootstrap。\n- Table4/TableS3：事后描述性分解。所有 QC 队列重叠，未进行独立组差异检验。\n- TableS5：训练/验证/测试人数按66个单元列出，合计不能当作参与者人数。\n\n## 方法边界\n\nLOSO 使用六个训练站点内一次85/15划分，选择后未在全六站上重新拟合。当前结果反映这套实际执行流程。完整复现仅从冻结时间序列和体积派生数据开始；原始 MRI 预处理、专家完整 QC、外部验证未由此建立。\n\n## 图注\n\n'''+''.join(f'### {k}\n\n{v}\n\n' for k,v in captions.items())
(B/'README_图表口径与图注.md').write_text(notes)
style='body{font:16px system-ui,sans-serif;color:#183044;margin:32px auto;max-width:1180px;line-height:1.6}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:8px;border-bottom:1px solid #dce4ea;text-align:left}th{background:#edf3f7;position:sticky;top:0}figure{margin:36px 0}img{max-width:100%}section{margin:32px 0}.scroll{overflow:auto}a{color:#126998}small{color:#526574}@media print{section,figure{break-inside:avoid}th{position:static}}'
def table(rows):
 keys=list(rows[0]);return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in keys)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x[k]))+'</td>' for k in keys)+'</tr>' for x in rows)+'</tbody></table></div>'
body='<h1>ADHD：Tables & Figures</h1><p>2026-09-14 · 研究分析用 · 冻结结果整理</p><p>4 张主表 + 10 张补充表；4 张主图 + 5 张补充图。CSV 可编辑，图可下载 PNG，具备矢量版本者附 PDF。</p><p><strong>Table 1 口径：</strong>连续变量为填补前统计；missing 为缺失人数。百分比分母为列内人数。三个 QC 队列重叠。头动阈值比例已转为百分比，TIV 已由 mm³ 转为 mL。</p><p><a href="README_图表口径与图注.md">统计口径、图注与限制</a></p>'
for name,title in [('Table1_primary_participants','Table 1. 主队列参与者特征'),('Table2_primary_model_performance','Table 2. 主队列模型表现'),('Table3_primary_contrast_by_QC','Table 3. QC 队列中的主要比较'),('Table4_QC_decomposition','Table 4. QC 变化的描述性分解')]:
 body+='<section><h2>'+title+'</h2><a href="tables/'+name+'.csv">下载 CSV</a>'+table(read(T/(name+'.csv')))+'</section>'
for name,caption in captions.items():
 if (F/(name+'.png')).exists():body+='<figure><h2>'+name+'</h2><a href="figures/'+name+'.png"><img src="figures/'+name+'.png"></a><figcaption>'+caption+'</figcaption>'+('<a href="figures/'+name+'.pdf">PDF</a>' if (F/(name+'.pdf')).exists() else '')+'</figure>'
body+='<h2>补充表</h2><ul>'+''.join('<li><a href="tables/'+p.name+'">'+p.stem+'</a></li>' for p in sorted(T.glob('TableS*.csv')) )+'</ul>'
(B/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ADHD Tables & Figures</title><style>'+style+'</style>'+body+'</html>')
# Verify source counts against prior released aggregate table.
for x in read(P/'cohort_site_counts.csv'):
 c=count(x['cohort'],x['site'],'ALL');assert int(c['n'])==int(x['n']) and int(c['label1_n'])==int(x['adhd']) and int(c['label0_n'])==int(x['control'])
validation={'unique_subject_counts_match_prior_21_site_cohort_rows':True,'source_manifest_hashes_match':all(hashlib.sha256((A/n).read_bytes()).hexdigest()==h for n,h in json.loads((A/'participant_aggregation_manifest.json').read_text())['files'].items()),'table_count':len(list(T.glob('*.csv'))),'figure_png_count':len(list(F.glob('*.png'))),'new_training':False,'manuscript_written':False}
(B/'validation.json').write_text(json.dumps(validation,indent=2));print(json.dumps(validation))
