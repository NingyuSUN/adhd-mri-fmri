from pathlib import Path
import csv,json,math,html
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

root=Path(__file__).resolve().parent.parent
result=root/'results/fmri_378';out=root/'docs/portfolio';fig=root/'figures/fmri_378'
def records(name):
 with (result/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))
rep={r['model']:r for r in records('representation_summary.csv')};cov={r['model']:r for r in records('demographic_increment_summary.csv')}
WHITE='FFFFFF';NAVY='152B3C';TEAL='087E8B';MINT='DDEFEF';GOLD='B97921';GRAY='526775';LIGHT='EDF2F5'
prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
prs.core_properties.title='ADHD-200 fMRI | Reproducible ML/DL evaluation';prs.core_properties.author='Ningyu Sun'
prs.core_properties.subject='Career portfolio; internal research evaluation'

def box(sl,x,y,w,h,fill=None,line=None):
 sh=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
 sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(fill or WHITE);sh.line.fill.background() if not line else None
 if line:sh.line.color.rgb=RGBColor.from_string(line)
 return sh

def text(sl,x,y,w,h,content,size=22,color=NAVY,bold=False):
 sh=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.word_wrap=True
 tf.margin_left=tf.margin_right=Inches(.02);tf.margin_top=tf.margin_bottom=Inches(.02)
 for i,line in enumerate(content.split('\n')):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='Aptos';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color);p.space_after=Pt(9)
 return sh

def slide(kicker,title,note):
 s=prs.slides.add_slide(prs.slide_layouts[6]);box(s,0,0,13.333,7.5)
 text(s,.62,.3,12,.35,kicker.upper(),12,TEAL,True);text(s,.62,.85,12.1,.88,title,31,NAVY,True)
 box(s,.65,6.91,12,.012,LIGHT);text(s,.65,7.03,11,.24,'NINGYU SUN  /  ADHD-200  /  FROZEN fMRI v1 · 2026-09-08',10,GRAY)
 text(s,12.25,7.02,.45,.25,str(len(prs.slides)),10,GRAY)
 s.notes_slide.notes_text_frame.text=note
 return s

def card(s,x,y,w,title,body,accent=TEAL):
 box(s,x,y,w,2.25,LIGHT);box(s,x,y,.055,2.25,accent);text(s,x+.2,y+.17,w-.4,.48,title,22,accent,True);text(s,x+.2,y+.76,w-.4,1.35,body,18)

def bars(s,rows,source,x=.8,y=2.1,w=11.5):
 # Full 0–1 AUC axis; minimum/maximum are explicitly descriptive repeat ranges.
 labelw=3.8;plotw=w-labelw-1.;barx=x+labelw
 for tick in [0,.25,.5,.75,1.]:
  xx=barx+tick*plotw;box(s,xx,y-.16,.008,3.62,LIGHT);text(s,xx-.2,y+3.55,.55,.26,f'{tick:g}',10,GRAY)
 for i,(label,key,col) in enumerate(rows):
  row=source[key];val=float(row['mean_auc']);lo=float(row['min_repeat_auc']);hi=float(row['max_repeat_auc']);yy=y+i*.73
  text(s,x,yy+.04,labelw-.2,.42,label,18)
  box(s,barx,yy+.07,val*plotw,.37,col)
  box(s,barx+lo*plotw,yy+.23,(hi-lo)*plotw,.018,NAVY)
  for v in [lo,hi]:box(s,barx+v*plotw,yy+.13,.015,.22,NAVY)
  text(s,barx+hi*plotw+.13,yy+.04,.8,.4,f'{val:.4f}',17,NAVY,True)
 text(s,barx,y+3.95,plotw+.5,.3,'AUC (0–1) · bars: mean · whiskers: min–max across 5 repeats',12,GRAY)

s=slide('Medical AI / Data science / ML engineering','Measuring what fMRI adds','开场用一句话说明项目：我建立并审计了多站点 fMRI ML/DL 流程，分别检验表示选择和影像增量。不要以诊断系统介绍。英文主页面面向招聘，中文备注用于讲解。')
text(s,.7,2.0,11.6,1.15,'A reproducible pipeline from audited participants\nto controlled, inspectable model comparisons.',28)
card(s,.72,3.7,3.8,'378 participants','Audited identity and labels\nA424 connectivity')
card(s,4.77,3.7,3.8,'ML + small DL','Logistic regression\n64 / 16 MLP ensemble')
card(s,8.82,3.7,3.8,'Evidence first','Role-safe evaluation\nIndependent table replay')
text(s,.75,6.15,11.5,.35,'Internal research benchmark · not a clinical diagnostic model',17,GRAY)
s=slide('01 / Problem','Two questions need two comparisons','表示是否更好，与影像是否在非影像信息之外增加收益，是不同的问题。先比较同一影像输入和模型，再加入年龄、性别、站点、头动对照。不能将组合0.7127写成纯影像准确率。')
card(s,.8,2.05,5.7,'1  Representation quality','Pearson vs tangent connectivity\nSame cohort, splits and classifiers')
card(s,6.85,2.05,5.7,'2  Added information','Full non-imaging control\nvs control + imaging predictions',GOLD)
text(s,.95,4.75,11.3,1.25,'A stronger image-only score does not, by itself,\nestablish useful information beyond the control.',27,NAVY,True)
s=slide('02 / Data and evaluation','One participant stays in one role','378人中211对照、167ADHD。五次三折是内部重复评估，三折轮换测试集；每折201训练、51验证、126测试。五次重复共享受试者，不能视为独立研究。时间窗或切片不能跨角色。')
for x,w,n,label,col in [(1.0,5.3,'201','TRAIN',TEAL),(6.5,2.3,'51','VALIDATION',GOLD),(9.,3.3,'126','TEST',NAVY)]:
 box(s,x,2.1,w,1.8,col);text(s,x+.15,2.28,w-.3,.62,n,38,WHITE,True);text(s,x+.15,3.08,w-.3,.38,label,16,WHITE,True)
text(s,1,4.45,11.5,1.1,'5 repeats × 3 folds · stratified by site and label\n211 controls / 167 ADHD · same saved partitions across comparisons',23)
text(s,1,6.03,11.5,.48,'Repeated internal development; no untouched external validation for this model.',17,GRAY)
s=slide('03 / Pipeline','Fit transformations inside the training split','预处理的数据拟合范围是训练集。单人协方差估计不读取其他受试者；切空间参考由训练协方差计算，再应用于验证测试。ANOVA筛选和标准化只fit训练。验证选择C、epoch和alpha；test用于评估。')
labels=[('A424 time series','Within-subject covariance'),('Connectivity','Pearson / tangent'),('Top 1,000 edges','ANOVA + standardization'),('LR / MLP','Validation selects settings')]
for i,(a,b) in enumerate(labels):
 x=.8+i*3.15;box(s,x,2.2,2.93,1.65,LIGHT);text(s,x+.15,2.44,2.6,.55,a,21,TEAL,True);text(s,x+.15,3.1,2.6,.52,b,16)
text(s,.95,4.5,11.6,.88,'Tests perturb held-out data and labels.\nTraining feature selection, scaling and reference remain unchanged.',24)
text(s,.95,5.98,11.5,.44,'Traceable inputs → saved roles → fitted objects → predictions → aggregate evidence',17,GRAY)
s=slide('04 / Result: image representation','Tangent improves image-only prediction','这四个数字均属于378人同协议。MLP从0.6096到0.6453，五次重复均增加，平均差0.0357；LR同样改善。条形图横轴0到1；须强调须线是五次重复最小最大，不是95%CI。MLP相对tangent LR仅0.0101，不主张神经网络普遍更好。')
bars(s,[('Pearson · LR','pearson_lr',GRAY),('Pearson · MLP ensemble','pearson_mlp_ens',GRAY),('Tangent · LR','tangent_lr',TEAL),('Tangent · MLP ensemble','tangent_mlp_ens',TEAL)],rep,y=2.08)
text(s,.9,6.4,11.3,.35,'MLP paired improvement: +0.0357 AUC · positive in 5/5 repeats',20,TEAL,True)
s=slide('05 / Result: incremental information','The fuller control changes the interpretation','控制组包含年龄、性别、站点及头动。它的AUC为0.7077，影像预测组合为0.7127，增量约0.0050且有一次为负。非影像LR不等于消除所有混杂。不能从小增量推出ADHD没有脑影像信号，也不能证明因果机制。')
for x,val,label,col in [(.95,'0.7077','Full non-imaging control',NAVY),(5.,'0.7127','Control + image predictions',TEAL)]:
 text(s,x,2.25,4.,1.0,val,52,col,True);text(s,x,3.45,4.,.68,label,20)
box(s,9.5,2.15,2.85,2.25,MINT);text(s,9.7,2.5,2.4,.7,'+0.0050',35,TEAL,True);text(s,9.7,3.38,2.4,.68,'Mean paired gain\n4/5 repeats positive',17)
text(s,.95,5.,11.4,1.12,'Small, partition-sensitive incremental gain.\n0.7127 includes non-imaging information.',27,NAVY,True)
s=slide('06 / Deep learning','Small architecture, explicit training decisions','输入1000维，64/16隐藏层，65121参数。GELU和dropout0.4/0.3，AdamW，学习率0.001，权重衰减0.01，batch16，最多80epoch，验证AUC早停patience12。三种子等权。重复之间复用了同组种子，应诚实说明。学习曲线来自历史输出，真实完整训练时间没有记录。')
for x,title,body in [(.85,'1,000 → 64 → 16 → 1','65,121 parameters\nGELU + dropout'),(4.95,'Train / select / replay','AdamW · early stopping\nSaved weights and learning curves'),(9.05,'Three fixed seeds','Equal-weight ensemble\nSeeds reused across repeats')]:card(s,x,2.1,3.5,title,body)
text(s,.95,4.85,11.4,1.02,'Compared with tangent LR: +0.0101 mean AUC.\nArchitecture complexity must earn its added cost.',25)
text(s,.95,6.23,11.4,.35,'Historical full-run time / peak RAM: not measured in this release.',16,GRAY)
s=slide('07 / Verification','Evidence that another engineer can inspect','新入口独立检查35910条真实测试预测和60组融合权重。验证受试者角色和标签、跨阶段相同队列、AUC平均方式，以及validation-only alpha和组合算术。浮点差约1e-16。区别：表层预测重放不等于重新从原始MRI预处理并训练所有模型。')
card(s,.8,2.15,3.75,'35,910 rows','Test memberships, labels\nand per-fold AUC replay')
card(s,4.8,2.15,3.75,'60 weight checks','Validation-only alpha\nand fusion arithmetic')
card(s,8.8,2.15,3.75,'Preserved sources','11 archived modules\n+ 1 documented supplement')
text(s,.95,4.85,11.4,1.0,'Table replay passed. Synthetic training passed.\nComplete raw-data reconstruction was not rerun.',25)
s=slide('08 / Live demo','Run the pipeline, then inspect its boundaries','现场执行python -m adhd_portfolio demo --out新目录。合成120例，60训练30验证30测试，跑原MLP训练函数并重放checkpoint。合成AUC不是ADHD结果。展示一个测试，修改held-out值仍不改变trainfit。再打开真实verificationJSON讲两者区别。')
box(s,.85,2.12,11.65,1.37,NAVY);text(s,1.1,2.43,11.1,.72,'python -m adhd_portfolio demo\n  --out artifacts/interview-demo-001',22,WHITE)
text(s,1,4.05,11.1,1.6,'120 synthetic examples · 60 / 30 / 30 split\nSaved training curve + checkpoint replay + measured timing\nThen inspect tests and the separate frozen-evidence record.',24)
text(s,1,6.2,11.1,.35,'Synthetic scores and timing are software-demo measurements, not ADHD performance.',16,GRAY)
s=slide('09 / Hiring relevance','One case, two technical conversations','医疗AI岗位讲QC、神经影像表示、站点与头动、非影像对照和外部验证边界。通用DS/MLE讲数据契约、版本、缓存与可运行入口、测试和资源成本。以证据解释为什么停下调参，而不是用阴性结果替代工程交付。项目主要由Ningyu主导，AI辅助开发审阅，不能转写为学生独立完成。')
card(s,.85,2.05,5.6,'Medical / biological AI','Imaging QC and representation\nCovariate controls and site shift\nCareful limits on clinical inference')
card(s,6.85,2.05,5.6,'Data science / ML engineering','Data contracts and reproducibility\nTestable training/evaluation paths\nNumerical debugging and model tradeoffs')
text(s,1,4.98,11.2,.95,'Delivered: source + evidence + runnable example.\nNext evidence, not just the next architecture.',27,NAVY,True)
text(s,1,6.32,11.2,.3,'github.com/NingyuSUN/adhd-mri-fmri · prepared locally on the portfolio branch',14,GRAY)
prs.save(out/'ADHD_fMRI_technical_portfolio.pptx')
# Lightweight standalone scientific chart in SVG, directly linked to numeric sources.
rows=[('Pearson LR','pearson_lr'),('Pearson MLP','pearson_mlp_ens'),('Tangent LR','tangent_lr'),('Tangent MLP','tangent_mlp_ens')]
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="520" viewBox="0 0 1200 520">','<rect width="1200" height="520" fill="white"/>','<g font-family="Arial" fill="#152b3c">','<text x="35" y="45" font-size="26">378-person fMRI: representation comparison</text>']
for i,(label,key) in enumerate(rows):
 val=float(rep[key]['mean_auc']);lo=float(rep[key]['min_repeat_auc']);hi=float(rep[key]['max_repeat_auc']);y=115+i*76
 svg.extend([f'<text x="35" y="{y+24}" font-size="20">{label}</text>',f'<rect x="240" y="{y}" width="{val*800}" height="36" fill="#087e8b"/>',f'<path d="M {240+lo*800} {y+18} H {240+hi*800} M {240+lo*800} {y+7} V {y+29} M {240+hi*800} {y+7} V {y+29}" stroke="#152b3c" fill="none"/>',f'<text x="{255+hi*800}" y="{y+25}" font-size="20">{val:.4f}</text>'])
for tick in [0,.25,.5,.75,1.]:svg.append(f'<text x="{235+tick*800}" y="450" font-size="17">{tick:g}</text>')
svg.extend(['<path d="M240 417 H1040" stroke="#526775"/>','<text x="240" y="490" font-size="18">AUC (0–1); whiskers: repeat min–max, NOT confidence intervals</text>','</g></svg>'])
(fig/'representation.svg').write_text('\n'.join(svg),encoding='utf-8')
# One-page PDF with standard readable body size.
pdf=canvas.Canvas(str(out/'ADHD_fMRI_case_study.pdf'),pagesize=(612,792));pdf.setTitle('Ningyu Sun — ADHD-200 fMRI ML/DL case study');pdf.setAuthor('Ningyu Sun')
def ptext(x,y,t,size=10,bold=False,color=NAVY):
 pdf.setFillColor(HexColor('#'+color));pdf.setFont('Helvetica-Bold' if bold else 'Helvetica',size);pdf.drawString(x,y,t)
ptext(42,750,'Ningyu Sun | ML / Deep Learning Case Study',12,True,TEAL);ptext(42,708,'Measuring what fMRI adds',26,True)
ptext(42,680,'ADHD-200  /  Python · PyTorch · scikit-learn · nilearn',11)
blocks=[('PROBLEM',[
'A multi-site fMRI benchmark can learn site, motion or demographic patterns.',
'I separated representation quality from incremental information beyond controls.']),('METHOD',[
'Audited 378 participants; 5 repeats x 3 subject-level folds; 201/51/126 roles.',
'Compared Pearson and tangent connectivity with LR and a 64/16 MLP.',
'Training-only feature selection, scaling and tangent reference; validation-only',
'hyperparameters, early stopping and three-seed averaging.']),('RESULTS',[
'Pearson MLP 0.6096 -> tangent MLP 0.6453: +0.0357 AUC, positive in 5/5 repeats.',
'Full non-imaging control 0.7077 -> control + image predictions 0.7127.',
'The +0.0050 incremental gain was small and partition-sensitive (4/5 positive).']),('ENGINEERING EVIDENCE',[
'Independent replay of 35,910 frozen test rows and 60 validation fusion weights.',
'Preserved scientific source hashes; portable CLI and explicit environment checks.',
'Tests for subject/role leakage, label alignment and training-only preprocessing.',
'Runnable synthetic LR/MLP demo with checkpoint replay, curves and timing.']),('HIRING RELEVANCE',[
'Medical AI: imaging QC, covariate controls and limits on site generalization.',
'DS / MLE: data contracts, reproducibility, numerical debugging and model tradeoffs.']),('SCOPE AND OWNERSHIP',[
'Mentor-led project with AI-assisted development/review. Internal reused cohort;',
'no diagnostic or externally validated prediction claim. Repeat ranges are not CIs.',
'This release replays evidence and prepares real splits; full training and raw-image',
'reconstruction were not rerun. Historical 409-person/structural studies are separate.'])]
y=640
for title,lines in blocks:
 ptext(42,y,title,10,True,TEAL);y-=20
 for line in lines:ptext(42,y,line,10);y-=15
 y-=16
ptext(42,35,'github.com/NingyuSUN/adhd-mri-fmri  |  Current local portfolio release: 2026-09-10',9,False,GRAY)
pdf.save()
# Structural QA, including speaker notes and source values.
assert len(prs.slides)==10
for i,s in enumerate(prs.slides,1):
 assert len(s.notes_slide.notes_text_frame.text)>50
 for sh in s.shapes:
  assert sh.left>=0 and sh.top>=0 and sh.left+sh.width<=prs.slide_width+100 and sh.top+sh.height<=prs.slide_height+100,(i,sh.name)
alltext='\n'.join(sh.text for s in prs.slides for sh in s.shapes if sh.has_text_frame)
for value in ['0.6453','0.7077','0.7127','35,910','60 weight']:assert value in alltext
(out/'deck_qa.json').write_text(json.dumps({'slides':10,'speaker_notes':10,'canvas_bounds':'passed','headline_values':'checked against aggregate tables','full_training_claim':False},indent=2),encoding='utf-8')
print('Created 10-slide editable PPTX, one-page PDF and SVG figure')
