"""Fixed-window CNN/TCN experiment on the preceding subject partitions."""
import argparse,copy,hashlib,json,subprocess,sys,time
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.metrics import roc_auc_score,average_precision_score,balanced_accuracy_score
import temporal_models as architecture
from temporal_models import Series,TemporalNet,predict_subjects,WINDOW
from run_connectivity import rank_auc
from run_paired import seed_all

CONFIG={"version":"temporal_v1","models":["cnn","tcn"],"window_samples":128,
    "sample_interval_seconds":1.0,"train_windows":"One random contiguous crop per subject per epoch",
    "primary_inference":"Mean probabilities from 5 fixed evenly spaced windows per subject",
    "secondary_inference":"Center window using the same checkpoint; not separately selected",
    "normalization":"Full-scan within-subject per-ROI z-score, no cohort fitted statistics",
    "hidden_channels":32,"blocks":3,"kernel_size":5,"cnn_dilations":[1,1,1],"tcn_dilations":[1,2,4],
    "epochs":60,"patience":12,"learning_rate":.0003,"weight_decay":.01,"batch_size":16,
    "seed":"1200+fold for each architecture; same crop RNG schedule","cpu_threads":4,
    "checkpoint_selection":"Inner-validation subject mean-5-window AUC only, earliest tie within 1e-4",
    "primary_comparisons":["cnn_mean5 vs historical_fmri_rbf","tcn_mean5 vs historical_fmri_rbf"],
    "caveat":"Exploratory repeatedly used cohort, not independent clinical validation."}
REFERENCES=["historical_fmri_rbf","fc_pca_mlp"]
def write_json(path,obj):path.write_text(json.dumps(obj,indent=2,default=str),encoding="utf-8")
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def fit(kind,series,y,tr,va,fold,device,out,factory=None,seed=None):
    seed=1200+fold if seed is None else seed
    seed_all(seed);rng=np.random.default_rng(seed)
    model=(TemporalNet(kind) if factory is None else factory()).to(device)
    optimizer=torch.optim.AdamW(model.parameters(),lr=.0003,weight_decay=.01)
    weight=torch.tensor(float((y[tr]==0).sum()/(y[tr]==1).sum()),device=device)
    criterion=nn.BCEWithLogitsLoss(pos_weight=weight)
    target=torch.from_numpy(y.astype(np.float32)).to(device)
    best=-np.inf;best_state=None;best_epoch=0;wait=0;history=[];crops=[]
    start=time.perf_counter()
    for epoch in range(1,61):
        model.train();total=0;count=0
        order=rng.permutation(tr)
        for first in range(0,len(order),16):
            idx=order[first:first+16]
            starts=np.array([rng.integers(0,series.lengths[i]-WINDOW+1) for i in idx])
            crops.extend({"epoch":epoch,"index":int(i),"start":int(s)} for i,s in zip(idx,starts))
            xb=series.batch(idx,starts).to(device);optimizer.zero_grad()
            loss=criterion(model(xb),target[idx])
            assert torch.isfinite(loss)
            loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step()
            total+=float(loss.detach())*len(idx);count+=len(idx)
        mean_p,_,_=predict_subjects(model,series,va)
        auc=roc_auc_score(y[va],mean_p)
        history.append({"epoch":epoch,"train_loss":total/count,"validation_subject_auc":auc})
        if auc>best+1e-4:
            best=auc;best_epoch=epoch
            best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
            wait=0
        else:wait+=1
        pd.DataFrame(history).to_csv(out/f"fold{fold}_{kind}_training.csv",index=False)
        if epoch%5==0:print(f"fold={fold} {kind} epoch={epoch} val_subject_auc={auc:.3f}",flush=True)
        if wait>=12:break
    model.load_state_dict(best_state)
    torch.save(best_state,out/f"fold{fold}_{kind}_weights.pt")
    crop_frame=pd.DataFrame(crops)
    assert set(crop_frame["index"])==set(tr)
    crop_frame.to_csv(out/f"fold{fold}_{kind}_train_crops.csv",index=False)
    info={"epochs_run":epoch,"best_epoch":best_epoch,"best_validation_auc":best,
        "parameters":sum(p.numel() for p in model.parameters()),"fit_seconds":time.perf_counter()-start}
    return model,info

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--reference",type=Path,required=True)
    parser.add_argument("--device",choices=["cpu","cuda"],default="cpu")
    parser.add_argument("--smoke",action="store_true")
    args=parser.parse_args();torch.set_num_threads(4)
    assert args.device!="cuda" or torch.cuda.is_available(),"CUDA not available"
    meta=json.loads((args.cache/"verification.json").read_text())
    assert meta["sample_interval_seconds"]==1.0 if "sample_interval_seconds" in meta else meta["effective_sample_interval_seconds"]==1.0
    assert digest(args.cache/"timeseries.npz")==meta["cache_sha256"]
    cohort=pd.read_csv(args.cache/"cohort.csv",dtype={"subject_id":str})
    ids=cohort.subject_id.to_numpy();y=cohort.label.to_numpy(np.int64)
    with np.load(args.cache/"timeseries.npz",allow_pickle=False) as cache:
        np.testing.assert_array_equal(ids,cache["subject_id"])
        series=Series(cache["data"],cache["offsets"])
        np.testing.assert_array_equal(series.lengths,cache["lengths"])
    assert len(ids)==409 and cohort.subject_id.is_unique
    old_protocol=json.loads((args.reference/"protocol.json").read_text())
    assert Path(old_protocol["feature_directory"]).resolve()==Path(meta["source_feature_directory"]).resolve()
    assert json.loads((args.reference/"complete.json").read_text())["status"]=="complete"
    previous_cohort=pd.read_csv(Path(old_protocol["feature_directory"])/"cohort.csv",dtype={"subject_id":str})
    pd.testing.assert_frame_equal(cohort,previous_cohort)
    split=pd.read_csv(args.reference/"splits.csv")
    lookup={sid:i for i,sid in enumerate(ids)};partitions=[]
    for fold in [1,2,3,4]:
        role_indices=[]
        for role in ["train","validation","test"]:
            frame=split[(split.fold==fold)&(split.role==role)]
            idx=np.array([lookup[sid] for sid in frame.subject_id],dtype=int)
            assert np.array_equal(frame.label.to_numpy(),y[idx])
            role_indices.append(idx)
        tr,va,te=role_indices
        assert not(set(tr)&set(va) or set(tr)&set(te) or set(va)&set(te))
        assert len(tr)+len(va)+len(te)==409
        partitions.append((fold,tr,va,te))
    assert sorted(np.concatenate([p[3] for p in partitions]).tolist())==list(range(409))
    out=Path(__file__).parent/"runs"/datetime.now().strftime("temporal_cv_%Y%m%d_%H%M%S")
    out.mkdir(parents=True,exist_ok=False)
    protocol={**CONFIG,"cache_directory":str(args.cache),"cache_sha256":meta["cache_sha256"],
        "reference_directory":str(args.reference),"split_sha256":digest(args.reference/"splits.csv"),
        "device":args.device,"smoke_only":args.smoke,"reused_references":REFERENCES,
        "packages":subprocess.check_output([sys.executable,"-m","pip","freeze"],text=True)}
    write_json(out/"protocol.json",protocol)
    (out/"splits.csv").write_bytes((args.reference/"splits.csv").read_bytes())
    (out/"experiment_source.py").write_text(Path(__file__).read_text(encoding="utf-8"),encoding="utf-8")
    (out/"architecture_source.py").write_text(Path(architecture.__file__).read_text(encoding="utf-8"),encoding="utf-8")
    pd.DataFrame({"index":np.arange(len(ids)),"subject_id":ids}).to_csv(out/"index_to_subject.csv",index=False)
    if args.smoke:
        tr=partitions[0][1];measurements=[]
        for kind in ["cnn","tcn"]:
            seed_all(1201);model=TemporalNet(kind).to(args.device)
            optimizer=torch.optim.AdamW(model.parameters(),lr=.0003)
            times=[]
            for step in range(8):
                idx=tr[:16];starts=(series.lengths[idx]-WINDOW)//2
                xb=series.batch(idx,starts).to(args.device);target=torch.from_numpy(y[idx].astype(np.float32)).to(args.device)
                if args.device=="cuda":torch.cuda.synchronize()
                start=time.perf_counter();optimizer.zero_grad()
                loss=nn.functional.binary_cross_entropy_with_logits(model(xb),target)
                loss.backward();optimizer.step()
                if args.device=="cuda":torch.cuda.synchronize()
                times.append(time.perf_counter()-start);assert torch.isfinite(loss)
            measurements.append({"model":kind,"median_step_seconds":float(np.median(times[2:])),
                "parameters":sum(p.numel() for p in model.parameters()),"training_subjects_only":True})
        write_json(out/"smoke.json",measurements);print(json.dumps(measurements,indent=2));print("OUTPUT",out);return
    rows=[];preds=[];window_rows=[];started=time.perf_counter()
    for fold,tr,va,te in partitions:
        for kind in ["cnn","tcn"]:
            print(f"START fold={fold} {kind}",flush=True)
            model,info=fit(kind,series,y,tr,va,fold,args.device,out)
            mean_p,center_p,windows=predict_subjects(model,series,te)
            for row in windows:
                i=row.pop("index")
                window_rows.append({"fold":fold,"architecture":kind,"subject_id":ids[i],"y":int(y[i]),**row})
            for evaluation,p in [("mean5",mean_p),("center",center_p)]:
                name=kind+"_"+evaluation
                rows.append({"fold":fold,"model":name,"source":"new_training_shared_checkpoint",
                    "auc":roc_auc_score(y[te],p),"ap":average_precision_score(y[te],p),
                    "balanced_accuracy":balanced_accuracy_score(y[te],p>=.5),
                    "n_train":len(tr),"n_validation":len(va),"n_test":len(te),**info})
                preds.extend({"fold":fold,"model":name,"subject_id":ids[i],"site":cohort.site.iloc[i],
                    "y":int(y[i]),"probability":float(v),"source":"new_training_shared_checkpoint"}
                    for i,v in zip(te,p))
            _,_,vw=predict_subjects(model,series,va)
            pd.DataFrame([{"subject_id":ids[r["index"]],"y":int(y[r["index"]]),**r} for r in vw]).to_csv(out/f"fold{fold}_{kind}_best_validation_windows.csv",index=False)
            pd.DataFrame(rows).to_csv(out/"new_fold_metrics.csv",index=False)
            pd.DataFrame(preds).to_csv(out/"new_predictions.csv",index=False)
            pd.DataFrame(window_rows).to_csv(out/"test_window_predictions.csv",index=False)
            print(f"TEST fold={fold} {kind} mean5_auc={rows[-2]['auc']:.4f} center_auc={rows[-1]['auc']:.4f}",flush=True)
    ref_rows=pd.read_csv(args.reference/"fold_metrics.csv")
    ref_pred=pd.read_csv(args.reference/"predictions.csv")
    ref_rows=ref_rows[ref_rows.model.isin(REFERENCES)].assign(source="reused_reference")
    ref_pred=ref_pred[ref_pred.model.isin(REFERENCES)].assign(source="reused_reference")
    all_rows=pd.concat([pd.DataFrame(rows),ref_rows],ignore_index=True)
    all_pred=pd.concat([pd.DataFrame(preds),ref_pred],ignore_index=True)
    all_rows.to_csv(out/"fold_metrics.csv",index=False);all_pred.to_csv(out/"predictions.csv",index=False)
    summary=all_rows.groupby(["model","source"]).agg(mean_auc=("auc","mean"),sd_auc=("auc","std"),
        mean_ap=("ap","mean"),mean_balanced_accuracy=("balanced_accuracy","mean")).reset_index()
    for i,row in summary.iterrows():
        frame=all_pred[all_pred.model==row.model].set_index("subject_id").loc[ids]
        assert len(frame)==409 and frame.index.is_unique and np.array_equal(frame.y.to_numpy(),y)
        summary.loc[i,"pooled_oof_auc"]=roc_auc_score(frame.y,frame.probability)
    summary.to_csv(out/"summary.csv",index=False)
    wide=all_pred.pivot(index="subject_id",columns="model",values="probability").loc[ids]
    strata=(cohort.site.astype(str)+"__"+cohort.label.astype(str)).to_numpy()
    groups=[[te[strata[te]==s] for s in np.unique(strata[te])] for _,_,_,te in partitions]
    rng=np.random.default_rng(2026)
    repeats=[[np.concatenate([rng.choice(g,len(g),replace=True) for g in fold_groups])
        for fold_groups in groups] for _ in range(1000)]
    pairs=[("cnn_mean5","historical_fmri_rbf"),("tcn_mean5","historical_fmri_rbf"),
        ("tcn_mean5","cnn_mean5"),("cnn_mean5","cnn_center"),("tcn_mean5","tcn_center")]
    comparisons=[]
    for candidate,reference in pairs:
        a=wide[candidate].to_numpy();b=wide[reference].to_numpy()
        observed=np.mean([rank_auc(y[te],a[te])-rank_auc(y[te],b[te]) for _,_,_,te in partitions])
        values=[np.mean([rank_auc(y[idx],a[idx])-rank_auc(y[idx],b[idx]) for idx in repeat]) for repeat in repeats]
        comparisons.append({"candidate":candidate,"reference":reference,"mean_fold_auc_difference":observed,
            "conditional_ci_low":np.quantile(values,.025),"conditional_ci_high":np.quantile(values,.975),
            "primary":reference=="historical_fmri_rbf",
            "caveat":"Fixed-OOF conditional interval, no retraining/selection uncertainty or multiplicity correction."})
    pd.DataFrame(comparisons).to_csv(out/"paired_bootstrap.csv",index=False)
    # Independent readback of predictions, subject IDs, and within-subject window aggregation.
    saved=pd.read_csv(out/"predictions.csv");saved_rows=pd.read_csv(out/"fold_metrics.csv")
    windows=pd.read_csv(out/"test_window_predictions.csv")
    assert len(saved)==2454 and len(rows)==16 and len(windows)==4090
    assert not saved.duplicated(["model","subject_id"]).any()
    for (model,fold),frame in saved.groupby(["model","fold"]):
        te=partitions[int(fold)-1][3];assert set(frame.subject_id)==set(ids[te])
        frame=frame.set_index("subject_id").loc[ids[te]]
        assert np.array_equal(frame.y.to_numpy(),y[te])
        recorded=saved_rows[(saved_rows.model==model)&(saved_rows.fold==fold)].auc.iloc[0]
        assert abs(roc_auc_score(y[te],frame.probability)-recorded)<1e-12
    for (kind,sid),frame in windows.groupby(["architecture","subject_id"]):
        assert len(frame)==5
        mean_p=saved[(saved.model==kind+"_mean5")&(saved.subject_id==sid)].probability.iloc[0]
        center_p=saved[(saved.model==kind+"_center")&(saved.subject_id==sid)].probability.iloc[0]
        assert abs(frame.probability.mean()-mean_p)<1e-12
        assert len(frame[frame.is_center])==1
        assert abs(frame[frame.is_center].probability.iloc[0]-center_p)<1e-12
    write_json(out/"results_validation.json",{"status":"passed","trained_model_folds":8,
        "new_evaluation_model_folds":16,"total_evaluation_model_folds_with_references":24,
        "subject_predictions":2454,"test_window_predictions":4090,
        "checks":["saved partition and label agreement","no duplicate OOF subjects",
                  "all saved AUCs recomputed","all mean5/center predictions reconstructed from window scores"]})
    write_json(out/"complete.json",{"status":"complete","elapsed_seconds":time.perf_counter()-started})
    print(summary.to_string(index=False),flush=True);print("OUTPUT",out,flush=True)
if __name__=="__main__":main()
