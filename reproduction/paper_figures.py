"""Publication figures from aggregate sensitivity tables only."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LABELS={'primary':'Primary (n=350)','warning_free':'No warnings (n=302)','include_holds':'Include holds (n=375)'}
COLORS=['#245c8f','#dc8843','#47886b']


def save(fig,out,name):
    fig.savefig(out/(name+'.png'),dpi=180,bbox_inches='tight')
    fig.savefig(out/(name+'.pdf'),bbox_inches='tight')
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tables',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    d=pd.read_csv(a.tables/'qc_decomposition.csv')
    fig,axes=plt.subplots(1,3,figsize=(12.8,4.4),sharey=True)
    for ax,(_,r) in zip(axes,d.iterrows()):
        vals=[r.common_subject_model_shift,r.evaluation_composition_shift,r.weight_shift]
        ax.bar(np.arange(3),vals,color=COLORS,width=.65)
        ax.axhline(0,color='#444',lw=.8)
        ax.axhline(r.total_native_shift,color='#a23b3b',lw=1.2,ls='--',label=f'Total shift {r.total_native_shift:+.3f}')
        for i,v in enumerate(vals):ax.annotate(f'{v:+.3f}',(i,v),xytext=(0,5 if v>=0 else -14),textcoords='offset points',ha='center',fontsize=10)
        ax.set_xticks(np.arange(3));ax.set_xticklabels(['Trained-model\ncontribution','Evaluation\ncomposition','Site-weight\ncontribution'],fontsize=9)
        ax.set_title(f'{LABELS[r.cohort_a]} →\n{LABELS[r.cohort_b]}',fontsize=10)
        ax.legend(loc='lower right',fontsize=8,frameon=False)
        ax.set_ylim(-.15,.095)
    axes[0].set_ylabel('Change in paired AUC increment (B − A)')
    fig.suptitle('QC sensitivity persists on the same held-out subjects',fontsize=14)
    fig.text(.5,-.015,'Exact descriptive decomposition; fixed primary site weights. Model contribution includes training, tuning and optimization changes.',ha='center',fontsize=9)
    fig.tight_layout();save(fig,a.out,'F1_qc_decomposition')
    s=pd.read_csv(a.tables/'site_contributions.csv')
    order=s[s.cohort.eq('primary')].sort_values('fixed_weight',ascending=False).site.tolist()
    fig,ax=plt.subplots(figsize=(10.5,4.8))
    for j,co in enumerate(LABELS):
        ss=s[s.cohort.eq(co)].set_index('site').loc[order]
        ax.bar(np.arange(len(order))+(j-1)*.25,ss.fixed_contribution,width=.23,label=LABELS[co],color=COLORS[j])
    ax.axhline(0,color='#444',lw=.8);ax.set_xticks(np.arange(len(order)));ax.set_xticklabels(order)
    ax.set_ylabel('Contribution to ΔAUC at fixed primary site weights')
    ax.set_title('Site contributions under identical aggregation weights')
    ax.legend(frameon=False);fig.tight_layout();save(fig,a.out,'F2_site_contributions')
    q=pd.read_csv(a.tables/'cv_interval_audit.csv')
    rows=q[q.cohort.eq('primary')]
    fig,ax=plt.subplots(figsize=(9,4.4))
    for i,(_,r) in enumerate(rows.iterrows()):
        ax.errorbar(r.mean_delta,i,xerr=[[r.mean_delta-r.ci90_lo],[r.ci90_hi-r.mean_delta]],fmt='o',capsize=4,color=COLORS[i%3])
    ax.axvspan(-.02,.02,color='#dceadf');ax.axvline(0,color='#777',lw=.8)
    ax.set_yticks(range(len(rows)));ax.set_yticklabels([f'{"Original outer ratio" if r.ratio_definition.startswith("original") else "Actual-fit ratio sensitivity"}, df={int(r.df)}' for _,r in rows.iterrows()])
    ax.set_xlabel('Primary contrast ΔAUC with 90% corrected interval')
    ax.set_title('CV equivalence remains unestablished across interval specifications')
    fig.tight_layout();save(fig,a.out,'F3_cv_interval_sensitivity')

    path=a.tables/'selector_alpha_distribution.csv'
    if path.exists():
        h=pd.read_csv(path);h=h[h.framework.eq('loso')&h.unit.eq('site_NYU')]
        matrix=h.pivot(index='cohort',columns='alpha',values='probability').reindex(list(LABELS))
        fig,ax=plt.subplots(figsize=(8.3,3.5))
        im=ax.imshow(matrix.to_numpy(),cmap='Blues',vmin=0,vmax=1,aspect='auto')
        for i in range(len(matrix)):
            for j in range(len(matrix.columns)):
                v=matrix.iloc[i,j];ax.text(j,i,f'{v:.1%}',ha='center',va='center',color='white' if v>.55 else '#222')
        ax.set_yticks(range(3));ax.set_yticklabels([LABELS[x] for x in matrix.index])
        ax.set_xticks(range(len(matrix.columns)));ax.set_xticklabels([f'{v:g}' for v in matrix.columns])
        ax.set_xlabel('Final structural fusion weight selected from resampled validation data')
        ax.set_title('NYU: final fusion-weight selection is sensitive to the QC cohort')
        fig.colorbar(im,ax=ax,label='Selection frequency',pad=.02)
        fig.text(.5,-.01,'1,000 site-by-label validation bootstraps; fitted models and upstream selection fixed. No test-based selection.',ha='center',fontsize=8)
        fig.tight_layout();save(fig,a.out,'F4_NYU_selector_stability')

if __name__=='__main__':main()
