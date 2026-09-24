"""Connectivity-only ablation with the exact preceding partitions and training routine."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import torch
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score,average_precision_score,balanced_accuracy_score
from sklearn.preprocessing import StandardScaler
import run_paired as previous

VARIANTS=["raw_pearson_unsigned","band_pearson_unsigned","band_plv_unsigned"]
REFERENCES=["historical_fmri_rbf","signed_pearson_sage","node_mlp"]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path,obj):path.write_text(json.dumps(obj,indent=2,default=str),encoding="utf-8")
def rank_auc(y,p):
    positive=y==1;n1=int(positive.sum());n0=len(y)-n1
    assert n1>0 and n0>0
    return float((rankdata(p)[positive].sum()-n1*(n1+1)/2)/(n1*n0))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--graphs",type=Path,required=True)
    parser.add_argument("--reference",type=Path,required=True)
    args=parser.parse_args()
    torch.set_num_threads(4)
    graph_protocol=json.loads((args.graphs/"protocol.json").read_text())
    graph_verify=json.loads((args.graphs/"verification.json").read_text())
    assert digest(args.graphs/"graphs.npz")==graph_verify["graphs_sha256"]
    feature_path=Path(graph_protocol["feature_directory"])
    assert digest(feature_path/"features.npz")==graph_protocol["feature_sha256"]
    old_protocol=json.loads((args.reference/"protocol.json").read_text())
    assert old_protocol["feature_sha256"]==graph_protocol["feature_sha256"]
    assert json.loads((args.reference/"complete.json").read_text())["status"]=="complete"
    training_source=Path(previous.__file__).read_text(encoding="utf-8")
    assert training_source==(args.reference/"experiment_source.py").read_text(encoding="utf-8"),"Previous training code changed"
    cohort=pd.read_csv(feature_path/"cohort.csv",dtype={"subject_id":str})
    ids=cohort.subject_id.to_numpy();y=cohort.label.to_numpy(np.int64)
    with np.load(feature_path/"features.npz",allow_pickle=False) as cache:
        np.testing.assert_array_equal(cache["subject_id"],ids);node=cache["node"]
    with np.load(args.graphs/"graphs.npz",allow_pickle=False) as cache:
        np.testing.assert_array_equal(cache["subject_id"],ids)
        graphs={name:torch.from_numpy(cache[name]) for name in VARIANTS}
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
    out=Path(__file__).parent/"runs"/datetime.now().strftime("connectivity_cv_%Y%m%d_%H%M%S")
    out.mkdir(parents=True,exist_ok=False)
    (out/"experiment_source.py").write_text(Path(__file__).read_text(encoding="utf-8"),encoding="utf-8")
    (out/"frozen_training_source.py").write_text(training_source,encoding="utf-8")
    (out/"splits.csv").write_bytes((args.reference/"splits.csv").read_bytes())
    protocol={"version":"connectivity_cv_v1","graphs":str(args.graphs),"reference_run":str(args.reference),
        "new_models":VARIANTS,"reused_reference_models":REFERENCES,
        "primary_comparison":["band_plv_unsigned","band_pearson_unsigned"],
        "training":"Exact preceding graph routine; 40 epochs, patience=8, seed=1200+fold, lr=.0003, wd=.01, batch=16",
        "constant":"9 raw node features; 8833 parameters; per-training-fold scaler; split and sample order unchanged",
        "changes":"Only neighbours/edge message signs differ; no architecture, node-feature, seed, or threshold search",
        "split_sha256":digest(args.reference/"splits.csv"),"graphs_sha256":graph_verify["graphs_sha256"],
        "feature_sha256":graph_protocol["feature_sha256"],
        "bootstrap":"1000 paired resamples within fold x site x label; conditional mean-fold AUC difference",
        "caveat":"Exploratory reused-cohort study. Not external validation or exact published GraphSAGE reproduction.",
        "packages":subprocess.check_output([sys.executable,"-m","pip","freeze"],text=True)}
    write_json(out/"protocol.json",protocol)
    ones=torch.ones((409,424,16),dtype=torch.float32)
    rows=[];preds=[];start=time.perf_counter()
    for fold,tr,va,te in partitions:
        scaler=StandardScaler().fit(node[tr].reshape(-1,9))
        x=torch.from_numpy(scaler.transform(node.reshape(-1,9)).reshape(node.shape).astype(np.float32))
        with np.load(args.reference/f"fold{fold}_node_scaler.npz",allow_pickle=False) as old:
            np.testing.assert_allclose(scaler.mean_,old["mean"],rtol=0,atol=0)
            np.testing.assert_allclose(scaler.scale_,old["scale"],rtol=0,atol=0)
        for variant in VARIANTS:
            print(f"START fold={fold} variant={variant}",flush=True)
            variant_out=out/variant;variant_out.mkdir(exist_ok=True)
            inputs=[x,graphs[variant],ones]
            # The name selects the unchanged graph architecture; directories distinguish the new graph variants.
            model,info=previous.fit_neural("signed_pearson_sage",inputs,y,tr,va,1200+fold,variant_out,fold)
            p=previous.probabilities(model,inputs,te)
            assert np.isfinite(p).all() and len(p)==len(te)
            row={"fold":fold,"model":variant,"auc":roc_auc_score(y[te],p),
                "ap":average_precision_score(y[te],p),
                "balanced_accuracy":balanced_accuracy_score(y[te],p>=.5),
                "n_train":len(tr),"n_validation":len(va),"n_test":len(te),
                "source":"new_training",**info}
            rows.append(row)
            preds.extend({"fold":fold,"model":variant,"subject_id":ids[i],"site":cohort.site.iloc[i],
                "y":int(y[i]),"probability":float(v),"source":"new_training"} for i,v in zip(te,p))
            pd.DataFrame(rows).to_csv(out/"new_fold_metrics.csv",index=False)
            pd.DataFrame(preds).to_csv(out/"new_predictions.csv",index=False)
            print(f"TEST fold={fold} variant={variant} AUC={row['auc']:.4f}",flush=True)
    old_rows=pd.read_csv(args.reference/"fold_metrics.csv")
    old_pred=pd.read_csv(args.reference/"predictions.csv")
    old_rows=old_rows[old_rows.model.isin(REFERENCES)].assign(source="reused_reference")
    old_pred=old_pred[old_pred.model.isin(REFERENCES)].assign(source="reused_reference")
    all_rows=pd.concat([pd.DataFrame(rows),old_rows],ignore_index=True)
    all_pred=pd.concat([pd.DataFrame(preds),old_pred],ignore_index=True)
    all_rows.to_csv(out/"fold_metrics.csv",index=False);all_pred.to_csv(out/"predictions.csv",index=False)
    assert len(rows)==12 and len(preds)==1227 and len(all_pred)==2454
    assert not all_pred.duplicated(["model","subject_id"]).any()
    summary=all_rows.groupby(["model","source"]).agg(mean_auc=("auc","mean"),sd_auc=("auc","std"),
        mean_ap=("ap","mean"),mean_balanced_accuracy=("balanced_accuracy","mean"),seconds=("seconds","sum")).reset_index()
    for i,row in summary.iterrows():
        frame=all_pred[all_pred.model==row.model].set_index("subject_id").loc[ids]
        assert len(frame)==409 and np.array_equal(frame.y.to_numpy(),y)
        summary.loc[i,"pooled_oof_auc"]=roc_auc_score(frame.y,frame.probability)
    summary.to_csv(out/"summary.csv",index=False)
    wide=all_pred.pivot(index="subject_id",columns="model",values="probability").loc[ids]
    strata=(cohort.site.astype(str)+"__"+cohort.label.astype(str)).to_numpy()
    resampling_groups=[]
    for _,_,_,te in partitions:
        resampling_groups.append([te[strata[te]==s] for s in np.unique(strata[te])])
    rng=np.random.default_rng(2026)
    bootstrap_indices=[[np.concatenate([rng.choice(g,len(g),replace=True) for g in groups])
        for groups in resampling_groups] for _ in range(1000)]
    pairs=[("band_plv_unsigned","band_pearson_unsigned"),("band_pearson_unsigned","raw_pearson_unsigned"),
        ("raw_pearson_unsigned","signed_pearson_sage"),("band_plv_unsigned","historical_fmri_rbf"),
        ("band_plv_unsigned","node_mlp")]
    comparisons=[]
    for candidate,reference in pairs:
        a=wide[candidate].to_numpy();b=wide[reference].to_numpy()
        observed=np.mean([rank_auc(y[te],a[te])-rank_auc(y[te],b[te]) for _,_,_,te in partitions])
        deltas=[np.mean([rank_auc(y[idx],a[idx])-rank_auc(y[idx],b[idx]) for idx in repeat]) for repeat in bootstrap_indices]
        comparisons.append({"candidate":candidate,"reference":reference,"mean_fold_auc_difference":observed,
            "conditional_ci_low":np.quantile(deltas,.025),"conditional_ci_high":np.quantile(deltas,.975),
            "primary":candidate=="band_plv_unsigned" and reference=="band_pearson_unsigned",
            "caveat":"Conditional fixed-OOF resampling; excludes retraining/selection uncertainty; no multiplicity adjustment."})
    pd.DataFrame(comparisons).to_csv(out/"paired_bootstrap.csv",index=False)
    # Re-read written predictions, verify against saved partitions/labels, and recompute every test AUC.
    saved_pred=pd.read_csv(out/"predictions.csv");saved_rows=pd.read_csv(out/"fold_metrics.csv")
    for (model,fold),frame in saved_pred.groupby(["model","fold"]):
        te=partitions[int(fold)-1][3]
        assert set(frame.subject_id)==set(ids[te])
        frame=frame.set_index("subject_id").loc[ids[te]]
        assert np.array_equal(frame.y.to_numpy(),y[te])
        recorded=saved_rows[(saved_rows.model==model)&(saved_rows.fold==fold)].auc.iloc[0]
        assert abs(roc_auc_score(y[te],frame.probability)-recorded)<1e-12
        assert abs(rank_auc(y[te],frame.probability.to_numpy())-recorded)<1e-12
    write_json(out/"results_validation.json",{"status":"passed","new_model_folds":12,
        "total_model_folds_with_references":24,"predictions":2454,"subjects_per_model":409,
        "checks":["identical previous partitions and scaler","unique OOF subjects","labels and all AUCs rechecked","rank AUC matches sklearn"]})
    write_json(out/"complete.json",{"status":"complete","elapsed_seconds":time.perf_counter()-start})
    print(summary.to_string(index=False),flush=True);print("OUTPUT",out,flush=True)
if __name__=="__main__":main()

