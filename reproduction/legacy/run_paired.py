"""Frozen, paired CPU experiment. Test data never select parameters or epochs."""
import argparse, copy, hashlib, json, random, subprocess, time
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits

MODELS=["historical_fmri_rbf","fc_pca_logistic","fc_pca_mlp","node_mlp","signed_pearson_sage",
        "confounds_logistic","site_confounds_logistic"]
PROTOCOL={"version":"local_paired_v1","outer_folds":4,"outer_seed":2026,
    "inner_validation_fraction":0.15,"inner_seed":"900+fold",
    "stratification":"site x binary label, subject-level",
    "models":MODELS,"pca_components":32,"graph_neighbours":16,"node_hidden":32,"roi_embedding":8,
    "graph_epochs":40,"graph_patience":8,"mlp_epochs":80,"mlp_patience":12,
    "graph_lr":0.0003,"mlp_lr":0.001,"weight_decay":0.01,"batch_size":16,"cpu_threads":4,
    "historical_svm_C":0.3,"linear_C":0.03,
    "selection":"Fixed model configurations; best inner-validation AUC epoch, earliest tie. No test selection.",
    "interpretation":"Exploratory reused cohort; not external clinical validation or exact published GraphSAGE reproduction."}

def write_json(path,value):
    path.write_text(json.dumps(value,indent=2,default=str),encoding="utf-8")
def seed_all(seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
def splits(cohort):
    strata=(cohort.site.astype(str)+"__"+cohort.label.astype(str)).to_numpy()
    outer=StratifiedKFold(4,shuffle=True,random_state=2026)
    result=[]
    for fold,(tv,te) in enumerate(outer.split(np.zeros(len(cohort)),strata),1):
        inner=StratifiedShuffleSplit(1,test_size=.15,random_state=900+fold)
        a,b=next(inner.split(np.zeros(len(tv)),strata[tv]));tr,va=tv[a],tv[b]
        assert not(set(tr)&set(va) or set(tr)&set(te) or set(va)&set(te))
        assert len(tr)+len(va)+len(te)==len(cohort)
        for idx in [tr,va,te]: assert set(cohort.label.iloc[idx])=={0,1}
        result.append((fold,tr,va,te))
    assert sorted(np.concatenate([x[3] for x in result]).tolist())==list(range(len(cohort)))
    return result

class FCMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(32,64),nn.GELU(),nn.Dropout(.4),
            nn.Linear(64,16),nn.GELU(),nn.Dropout(.3),nn.Linear(16,1))
    def forward(self,x): return self.net(x).flatten()

class ROIModel(nn.Module):
    def __init__(self,use_graph):
        super().__init__();self.use_graph=use_graph
        self.roi=nn.Embedding(424,8)
        self.self_layers=nn.ModuleList([nn.Linear(17,32),nn.Linear(32,32)])
        self.neighbour_layers=nn.ModuleList([nn.Linear(17,32,bias=False),nn.Linear(32,32,bias=False)])
        self.norms=nn.ModuleList([nn.LayerNorm(32),nn.LayerNorm(32)])
        self.dropout=nn.Dropout(.3)
        self.head=nn.Sequential(nn.Linear(64,32),nn.GELU(),nn.Dropout(.3),nn.Linear(32,1))
    def forward(self,x,neighbours,signs):
        batch=x.shape[0]
        embedded=self.roi.weight.unsqueeze(0).expand(batch,-1,-1)
        h=torch.cat([x,embedded],-1)
        for own,other,norm in zip(self.self_layers,self.neighbour_layers,self.norms):
            if self.use_graph:
                gathered=h[torch.arange(batch)[:,None,None],neighbours]
                aggregate=(gathered*signs[:,:,:,None]).mean(2)
            else:
                # Self-only messages remove between-ROI connectivity while keeping the parameterization.
                aggregate=h
            h=self.dropout(torch.nn.functional.gelu(norm(own(h)+other(aggregate))))
        pooled=torch.cat([h.mean(1),h.std(1,unbiased=False)],-1)
        return self.head(pooled).flatten()

@torch.no_grad()
def probabilities(model,inputs,indices):
    model.eval();parts=[]
    for chunk in np.array_split(indices,max(1,int(np.ceil(len(indices)/32)))):
        parts.append(torch.sigmoid(model(*[x[chunk] for x in inputs])).numpy())
    return np.concatenate(parts)

def fit_neural(name,inputs,y,tr,va,seed,out,fold):
    seed_all(seed)
    model=FCMLP() if name=="fc_pca_mlp" else ROIModel(name=="signed_pearson_sage")
    max_epochs=80 if name=="fc_pca_mlp" else 40
    patience=12 if name=="fc_pca_mlp" else 8
    lr=.001 if name=="fc_pca_mlp" else .0003
    optimizer=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=.01)
    target=torch.from_numpy(y.astype(np.float32))
    positive_weight=torch.tensor(float((y[tr]==0).sum()/(y[tr]==1).sum()))
    criterion=nn.BCEWithLogitsLoss(pos_weight=positive_weight)
    rng=np.random.default_rng(seed);best=-np.inf;best_epoch=0;best_state=None;wait=0;history=[]
    start=time.perf_counter()
    for epoch in range(1,max_epochs+1):
        model.train();loss_sum=0;count=0
        order=rng.permutation(tr)
        for offset in range(0,len(order),16):
            batch=order[offset:offset+16]
            optimizer.zero_grad()
            logits=model(*[x[batch] for x in inputs])
            loss=criterion(logits,target[batch])
            assert torch.isfinite(loss),"Non-finite loss"
            loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step()
            loss_sum+=float(loss.detach())*len(batch);count+=len(batch)
        val=probabilities(model,inputs,va)
        auc=roc_auc_score(y[va],val)
        history.append({"epoch":epoch,"train_loss":loss_sum/count,"val_auc":auc})
        if auc>best+1e-4:
            best=auc;best_epoch=epoch;best_state=copy.deepcopy(model.state_dict());wait=0
        else:wait+=1
        if epoch%5==0:print(f"fold={fold} {name} epoch={epoch} val_auc={auc:.3f}",flush=True)
        if wait>=patience:break
    model.load_state_dict(best_state)
    torch.save(best_state,out/f"fold{fold}_{name}_weights.pt")
    pd.DataFrame(history).to_csv(out/f"fold{fold}_{name}_training.csv",index=False)
    return model,{"epochs_run":epoch,"best_epoch":best_epoch,"best_val_auc":best,
        "seconds":time.perf_counter()-start,"parameters":sum(p.numel() for p in model.parameters())}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--features",type=Path,required=True)
    parser.add_argument("--smoke",action="store_true")
    args=parser.parse_args()
    torch.set_num_threads(4)
    out=Path(__file__).parent/"runs"/datetime.now().strftime("paired_%Y%m%d_%H%M%S")
    out.mkdir(parents=True,exist_ok=False)
    (out/"experiment_source.py").write_text(Path(__file__).read_text(encoding="utf-8"),encoding="utf-8")
    cohort=pd.read_csv(args.features/"cohort.csv",dtype={"subject_id":str})
    verify=json.loads((args.features/"verification.json").read_text())
    assert verify["one_hz_mismatches"]==0
    assert verify["one_hz_unverified"]==0,"Complete sampling provenance before training this protocol"
    with np.load(args.features/"features.npz",allow_pickle=False) as bank:
        arrays={k:bank[k] for k in bank.files}
    assert np.array_equal(arrays["subject_id"],cohort.subject_id.to_numpy())
    assert np.array_equal(arrays["label"],cohort.label.to_numpy())
    assert hashlib.sha256((args.features/"features.npz").read_bytes()).hexdigest()==verify["cache_sha256"]
    protocol={**PROTOCOL,"feature_directory":str(args.features),"feature_sha256":verify["cache_sha256"],
        "smoke_only":args.smoke,"python_packages":subprocess.check_output([__import__("sys").executable,"-m","pip","freeze"],text=True)}
    write_json(out/"protocol.json",protocol)
    folds=splits(cohort);splitrows=[]
    for fold,tr,va,te in folds:
        for role,indices in [("train",tr),("validation",va),("test",te)]:
            splitrows.extend({"fold":fold,"role":role,"subject_id":cohort.subject_id.iloc[i],
                "site":cohort.site.iloc[i],"label":int(cohort.label.iloc[i])} for i in indices)
    pd.DataFrame(splitrows).to_csv(out/"splits.csv",index=False)
    y=cohort.label.to_numpy(np.int64)
    node=arrays["node"];neighbours=torch.from_numpy(arrays["neighbours"]);signs=torch.from_numpy(arrays["signs"])
    historical=np.c_[arrays["fc_summary"],arrays["spectral"],arrays["brainlm"]]
    confounds=cohort[["age","sex_male","mean_fd","max_fd","pct_fd_gt_0p2","mean_dvars","n_volumes","qc_rest"]].to_numpy(np.float32)
    siteconf=np.c_[pd.get_dummies(cohort.site,dtype=float).to_numpy(),confounds]
    if args.smoke:
        measurements=[]
        _,tr,va,te=folds[0]
        scaler=StandardScaler().fit(node[tr].reshape(-1,9))
        x=torch.from_numpy(scaler.transform(node.reshape(-1,9)).reshape(node.shape).astype(np.float32))
        for name in ["node_mlp","signed_pearson_sage"]:
            seed_all(2026);model=ROIModel(name=="signed_pearson_sage")
            optimizer=torch.optim.AdamW(model.parameters(),lr=.0003)
            durations=[]
            for step in range(8):
                batch=tr[:16];start=time.perf_counter();optimizer.zero_grad()
                output=model(x[batch],neighbours[batch],signs[batch])
                loss=nn.functional.binary_cross_entropy_with_logits(output,torch.from_numpy(y[batch].astype(np.float32)))
                loss.backward();optimizer.step();durations.append(time.perf_counter()-start)
                assert torch.isfinite(loss)
            measurements.append({"model":name,"median_step_seconds":float(np.median(durations[2:])),
                "parameters":sum(p.numel() for p in model.parameters()),
                "input_shape":[16,424,9],"note":"Training-only throughput test; no test-set evaluation."})
        write_json(out/"cpu_smoke.json",measurements);print(json.dumps(measurements,indent=2));print("OUTPUT",out);return
    records=[];predictions=[];details=[]
    for fold,tr,va,te in folds:
        print(f"FOLD {fold} train={len(tr)} validation={len(va)} test={len(te)}",flush=True)
        # All representations and fitted transformations use this same inner training subset.
        with threadpool_limits(limits=4):
            edge_scaler=StandardScaler().fit(arrays["fc_edges"][tr])
            transformed=edge_scaler.transform(arrays["fc_edges"])
            pca=PCA(32,svd_solver="randomized",random_state=2026).fit(transformed[tr])
            projected=pca.transform(transformed)
            pca_scaler=StandardScaler().fit(projected[tr])
            pc=pca_scaler.transform(projected).astype(np.float32)
        np.savez_compressed(out/f"fold{fold}_pca_transform.npz",edge_mean=edge_scaler.mean_,
            edge_scale=edge_scaler.scale_,pca_mean=pca.mean_,pca_components=pca.components_,
            projected_mean=pca_scaler.mean_,projected_scale=pca_scaler.scale_)
        nsc=StandardScaler().fit(node[tr].reshape(-1,9))
        nscaled=nsc.transform(node.reshape(-1,9)).reshape(node.shape).astype(np.float32)
        np.savez(out/f"fold{fold}_node_scaler.npz",mean=nsc.mean_,scale=nsc.scale_)
        node_inputs=[torch.from_numpy(nscaled),neighbours,signs]
        for name in MODELS:
            started=time.perf_counter();info={}
            if name in ["fc_pca_mlp","node_mlp","signed_pearson_sage"]:
                inputs=[torch.from_numpy(pc)] if name=="fc_pca_mlp" else node_inputs
                model,info=fit_neural(name,inputs,y,tr,va,1200+fold,out,fold)
                prediction=probabilities(model,inputs,te)
            else:
                X={"historical_fmri_rbf":historical,"fc_pca_logistic":pc,
                   "confounds_logistic":confounds,"site_confounds_logistic":siteconf}[name]
                estimator=SVC(C=.3,gamma="scale",class_weight="balanced",probability=True,random_state=42) if name=="historical_fmri_rbf" else LogisticRegression(C=.03,class_weight="balanced",max_iter=4000,solver="liblinear",random_state=42)
                pipeline=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),estimator)
                with threadpool_limits(limits=4):pipeline.fit(X[tr],y[tr])
                prediction=pipeline.predict_proba(X[te])[:,1]
                # Local trusted artifact, never load untrusted serialized estimators.
                import joblib
                joblib.dump(pipeline,out/f"fold{fold}_{name}.joblib")
            assert len(prediction)==len(te) and np.isfinite(prediction).all()
            record={"fold":fold,"model":name,"auc":roc_auc_score(y[te],prediction),
                "ap":average_precision_score(y[te],prediction),
                "balanced_accuracy":balanced_accuracy_score(y[te],prediction>=.5),
                "n_train":len(tr),"n_validation":len(va),"n_test":len(te),
                "seconds":time.perf_counter()-started,**info}
            records.append(record);details.append({"fold":fold,"model":name,**info})
            predictions.extend({"fold":fold,"model":name,"subject_id":cohort.subject_id.iloc[i],
                "site":cohort.site.iloc[i],"y":int(y[i]),"probability":float(p)} for i,p in zip(te,prediction))
            pd.DataFrame(records).to_csv(out/"fold_metrics.csv",index=False)
            pd.DataFrame(predictions).to_csv(out/"predictions.csv",index=False)
            print(f"TEST fold={fold} {name} auc={record['auc']:.4f} seconds={record['seconds']:.1f}",flush=True)
    df=pd.DataFrame(records);pred=pd.DataFrame(predictions)
    summary=df.groupby("model").agg(mean_auc=("auc","mean"),sd_auc=("auc","std"),mean_ap=("ap","mean"),
        mean_balanced_accuracy=("balanced_accuracy","mean"),total_seconds=("seconds","sum")).reset_index()
    for i,row in summary.iterrows():
        p=pred[pred.model==row.model].set_index("subject_id").loc[cohort.subject_id]
        assert p.index.is_unique and len(p)==409
        summary.loc[i,"pooled_oof_auc"]=roc_auc_score(p.y,p.probability)
    summary.to_csv(out/"summary.csv",index=False)
    # Paired, site-and-label-stratified subject bootstrap of fixed OOF predictions.
    # This conditional interval does not include training/split-selection uncertainty.
    wide=pred.pivot(index="subject_id",columns="model",values="probability").loc[cohort.subject_id]
    strata=(cohort.site.astype(str)+"__"+cohort.label.astype(str)).to_numpy()
    groups=[np.where(strata==s)[0] for s in np.unique(strata)]
    rng=np.random.default_rng(2026);comparisons=[]
    pairs=[(m,"historical_fmri_rbf") for m in ["fc_pca_logistic","fc_pca_mlp","node_mlp","signed_pearson_sage"]]+[("signed_pearson_sage","node_mlp")]
    for candidate,reference in pairs:
        deltas=[]
        for _ in range(1000):
            idx=np.concatenate([rng.choice(g,len(g),replace=True) for g in groups])
            deltas.append(roc_auc_score(y[idx],wide[candidate].to_numpy()[idx])-roc_auc_score(y[idx],wide[reference].to_numpy()[idx]))
        comparisons.append({"candidate":candidate,"reference":reference,
            "pooled_auc_difference":roc_auc_score(y,wide[candidate])-roc_auc_score(y,wide[reference]),
            "conditional_ci_low":np.quantile(deltas,.025),"conditional_ci_high":np.quantile(deltas,.975),
            "caveat":"Paired fixed-OOF subject bootstrap; not independent external validation or multiplicity-adjusted."})
    pd.DataFrame(comparisons).to_csv(out/"paired_bootstrap.csv",index=False)
    write_json(out/"complete.json",{"status":"complete","model_folds":len(df),"subjects_per_model":409,"models":MODELS})
    print(summary.to_string(index=False),flush=True);print("OUTPUT",out,flush=True)

if __name__=="__main__":main()

