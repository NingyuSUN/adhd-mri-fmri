"""Small synthetic training demonstration, deliberately separate from real AUCs."""
from pathlib import Path
import json,time,platform
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from .evidence import require
from .frozen import load_modules,environment

def run_demo(out):
    out=Path(out).resolve();require(not out.exists(),'Refusing existing demo output');out.mkdir(parents=True)
    modules=load_modules();neural=modules['run_functional_fusion'];features=modules['run_connectome_representations']
    import torch
    torch.set_num_threads(1)
    rng=np.random.default_rng(20260910);y=np.tile([0,1],60);x=rng.normal(size=(120,24));x[:,:3]+=y[:,None]*.7
    tv,te=train_test_split(np.arange(len(y)),test_size=.25,stratify=y,random_state=42)
    tr,va=train_test_split(tv,test_size=1/3,stratify=y[tv],random_state=43)
    transformed,order,scale=features.select_features(x,y,tr,k=12)
    rows=[];started=time.perf_counter()
    with threadpool_limits(limits=1):
        candidates=[LogisticRegression(C=c,class_weight='balanced',solver='liblinear',random_state=42).fit(transformed[tr],y[tr]) for c in [.01,.1,1.]]
        scores=[roc_auc_score(y[va],m.decision_function(transformed[va])) for m in candidates];best=next(i for i,v in enumerate(scores) if v>=max(scores)-1e-12)
        lr=candidates[best];lr_time=time.perf_counter()-started;lp=lr.predict_proba(transformed[te])[:,1]
        start=time.perf_counter();model,xt,info=neural.train_neural(transformed,y,tr,va,1,'synthetic_mlp',out,seed=1201)
        training_seconds=time.perf_counter()-start;mp=neural.predict(model,xt,te)
        checkpoint=torch.load(out/'fold1_synthetic_mlp.pt',weights_only=True);replay=neural.MLP(checkpoint['input_features']);replay.load_state_dict(checkpoint['state_dict'])
        np.testing.assert_allclose(neural.predict(replay,xt,te),mp,rtol=0,atol=1e-7)
        start=time.perf_counter()
        for _ in range(100):neural.predict(replay,xt,te)
        inference_ms=(time.perf_counter()-start)*1000/100
    for name,score in [('synthetic_lr',lp),('synthetic_mlp',mp)]:
        rows.extend(dict(model=name,synthetic_subject=f'demo-{i:03d}',y=int(y[i]),score=float(p)) for i,p in zip(te,score))
    pd.DataFrame(rows).to_csv(out/'synthetic_predictions.csv',index=False)
    result={'data':'SYNTHETIC; no ADHD subjects; these AUCs are software demonstration values only','seed':20260910,'subjects':120,'train':len(tr),'validation':len(va),'test':len(te),'raw_features':24,'selected_features':12,'lr_validation_selected_C':[.01,.1,1.][best],'synthetic_lr_auc':roc_auc_score(y[te],lp),'synthetic_mlp_auc':roc_auc_score(y[te],mp),'checkpoint_replay_passed':True,'lr_training_seconds':lr_time,'mlp_training_seconds':training_seconds,'mlp_batch30_inference_ms':inference_ms,'threads':1,'platform':platform.platform(),'mlp':info,'environment':environment(),'resource_note':'Wall-clock measurements from this synthetic run only. Peak RAM and historical full-run training time were not measured.'}
    (out/'demo.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result
