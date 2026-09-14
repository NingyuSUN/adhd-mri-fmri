from pathlib import Path
import sys,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(sys.argv[1]);d=json.loads(sys.stdin.read());plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42})
models=['full_covariates_lr','structural_lr','structural_mlp','tangent_lr','tangent_mlp','full_functional_mlp','full_fusion_structural_mlp'];rows={x['model']:x for x in d['cv']}
fig,ax=plt.subplots(figsize=(9,5))
for i,m in enumerate(models):
 x=rows[m];v=float(x['mean_auc']);ax.errorbar(v,i,xerr=[[v-float(x['min_repeat_auc'])],[float(x['max_repeat_auc'])-v]],fmt='o',color='#24678d',capsize=4)
ax.set_yticks(range(7),models,fontsize=9);ax.invert_yaxis();ax.set_xlabel('Mean fold AUC across five repeats');ax.set_title('Figure S1. Primary-cohort model performance');ax.axvline(.5,ls='--',color='#999');ax.grid(axis='x',alpha=.15);ax.spines[['top','right']].set_visible(False)
fig.text(.02,.02,'Bars: minimum to maximum repeat mean, not confidence intervals. Models match Table 2.\nBaseline uses site, motion, age and recorded sex; the 17-output full table is supplied separately.',fontsize=9);fig.tight_layout(rect=[0,.1,1,1])
for ext in ['png','pdf']:fig.savefig(p/('FigureS1_CV_models.'+ext),dpi=220,bbox_inches='tight')
plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(13,5),sharex=True);sites=['NYU','KKI','Peking_1','OHSU','NeuroIMAGE','Peking_2','Peking_3']
for ax,co in zip(axs,['primary','warning_free','include_holds']):
 rows={x['site']:x for x in d['site'] if x['cohort']==co and x['contrast']=='P'}
 for i,s in enumerate(sites):
  x=rows[s];v=float(x['delta']);ax.errorbar(v,i,xerr=[[v-float(x['ci95_lo'])],[float(x['ci95_hi'])-v]],fmt='o',capsize=3,color='#24678d')
 ax.set_yticks(range(7),[s+' (n='+rows[s]['n']+')' for s in sites],fontsize=8);ax.invert_yaxis();ax.axvspan(-.02,.02,color='#e5e9ed');ax.axvline(0,color='#999',lw=.8);ax.set_xlabel('Primary contrast (ΔAUC)');ax.set_title(co.replace('_',' '));ax.spines[['top','right']].set_visible(False)
fig.suptitle('Figure S5. Site-specific structural increment under LOSO',fontsize=14);fig.text(.02,.015,'95% within-site subject bootstrap intervals; fixed fitted models and observed sites.\nActual procedure: one inner holdout and no full training-site refit. Small-site intervals are imprecise.',fontsize=9);fig.tight_layout(rect=[0,.12,1,.92])
for ext in ['png','pdf']:fig.savefig(p/('FigureS5_LOSO_contrasts.'+ext),dpi=220,bbox_inches='tight')
plt.close(fig);print('Rendered revised S1 and S5')
