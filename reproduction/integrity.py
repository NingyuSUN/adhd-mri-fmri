"""Strict comparisons used by the independent reproduction runner."""
import hashlib
import numpy as np


def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def verify_manifest(root,hashes):
    for rel,want in hashes.items():
        if digest(root/rel)!=want:raise ValueError(f'hash mismatch: {rel}')
    return len(hashes)


def compare_predictions(old,new):
    key=['subject_id','model']
    if old.duplicated(key).any() or new.duplicated(key).any():raise ValueError('duplicate prediction keys')
    a=old.set_index(key).sort_index();b=new.set_index(key).sort_index()
    if not a.index.equals(b.index):raise ValueError('prediction subject/model keys differ')
    if not np.array_equal(a[['site','y']],b[['site','y']]):raise ValueError('prediction labels/sites differ')
    if not np.isfinite(a.score).all() or not np.isfinite(b.score).all():raise ValueError('nonfinite predictions')
    delta=np.abs(a.score.to_numpy()-b.score.to_numpy())
    return dict(rows=len(a),max_abs_score_difference=float(delta.max()),mean_abs_score_difference=float(delta.mean()),
                scores_match_rtol_1e_5_atol_1e_6=bool(np.allclose(a.score,b.score,rtol=1e-5,atol=1e-6)))
