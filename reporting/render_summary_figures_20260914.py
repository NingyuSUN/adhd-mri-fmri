"""Render aggregate-only publication figures. No model fitting."""
from pathlib import Path
import json,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
p=Path(sys.argv[1]); d=json.loads(sys.stdin.read());plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'pdf.fonttype':42,'svg.fonttype':'none'})
counts=d['counts'];qc=d['qc']
fig,ax=plt.subplots(figsize=(10,8));ax.set(xlim=(0,10),ylim=(0,9));ax.axis('off')
def box(x,y,w,h,t,fill='#edf3f7'):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.12,rounding_size=0.08',edgecolor='#25445b',facecolor=fill,lw=1.2));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=11)
def arrow(x,y,xx,yy):ax.annotate('',xy=(xx,yy),xytext=(x,y),arrowprops={'arrowstyle':'->','lw':1.3,'color':'#25445b'})
def txt(co,title):
 c=counts[co];return title+f"\nn = {c['n']} | ADHD label: {c['label1_n']} | Control: {c['label0_n']}"
box(.4,7.2,6.0,1.0,txt('reviewed','Frozen paired cohort entering structural QC'))
box(.4,5.2,6.0,1.0,txt('include_holds','Include-HOLD sensitivity cohort'))
box(.4,3.2,6.0,1.0,txt('primary','Primary analysis cohort'))
box(.4,1.2,6.0,1.0,txt('warning_free','Warning-free sensitivity cohort'))
for yy,label in [(6.7,'Image-quality failure\nexcluded: n = 3'),(4.7,'Anatomical-review HOLD\nexcluded: n = 25'),(2.7,'Signal-warning category\nexcluded: n = 48')]:
 arrow(3.4,yy+.5,3.4,yy-.5);arrow(3.4,yy,6.7,yy);box(6.9,yy-.4,2.7,.8,label,'#fff3e8')
ax.text(.3,8.65,'Figure 1. Participant flow and nested QC cohorts',fontsize=15,weight='bold')
ax.text(.4,.55,'The three analysis cohorts overlap; they are not independent samples.\nThe flow starts at the verified 378-person paired cohort, not initial dataset recruitment.',fontsize=10,color='#435362')
fig.savefig(p/'Figure1_participant_flow.png',dpi=220,bbox_inches='tight');fig.savefig(p/'Figure1_participant_flow.pdf',bbox_inches='tight');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,4.6),sharey=True)
cohorts=['primary','warning_free','include_holds'];labels=['Primary (n = 350)','Warning-free (n = 302)','Include HOLD (n = 375)']
for ax,framework,title in zip(axs,['CV','LOSO'],['Mixed-site repeated CV','Leave-one-site-out']):
 for i,co in enumerate(cohorts):
  x=d['contrast'][framework][co];v=x['delta'];lo=x['lo'];hi=x['hi'];ax.errorbar(v,i,xerr=[[v-lo],[hi-v]],fmt='o',capsize=4,color='#165d86',ms=6);ax.text(.02,.96-i*.09,f'{v:+.3f} [{lo:+.3f}, {hi:+.3f}]',transform=ax.transAxes,fontsize=9)
 ax.axvspan(-.02,.02,color='#e5e9ed');ax.axvline(0,color='#697780',lw=.8);ax.set_title(title);ax.set_yticks(range(3),labels);ax.set_ylim(2.5,-.9);ax.set_xlabel('Structural fusion − functional fusion (ΔAUC)');ax.grid(axis='x',alpha=.2);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Figure 2. Primary contrast across QC cohorts',fontsize=15)
fig.text(.02,.01,'90% intervals. CV: original corrected t interval (df = 14). LOSO: original within-site subject bootstrap.\nGrey band: ±0.02 equivalence margin. Intervals condition on different evaluation procedures; cohorts overlap.',fontsize=9)
fig.tight_layout(rect=[0,.13,1,.92]);fig.savefig(p/'Figure2_primary_contrast.png',dpi=220,bbox_inches='tight');fig.savefig(p/'Figure2_primary_contrast.pdf',bbox_inches='tight');plt.close(fig)
print('Rendered 2 PNG + 2 PDF files')
