import unittest
import importlib.util
import numpy as np
import pandas as pd

class ImplementationExists(unittest.TestCase):
    def test_evidence_module_is_implemented(self):
        self.assertIsNotNone(importlib.util.find_spec("adhd_fmri_benchmark.evidence"), "Evidence validation implementation is missing")

class EvidenceRules(unittest.TestCase):
    def setUp(self):
        if importlib.util.find_spec("adhd_fmri_benchmark.evidence") is None:
            self.skipTest("implementation not yet present")
        from adhd_fmri_benchmark.evidence import validate_tables, aggregate
        self.validate, self.aggregate = validate_tables, aggregate
        self.c = pd.DataFrame({"subject_id":list("abcdefgh"),"label":[0,1]*4,"site":["A"]*8})
        splits=[];pred=[]
        for f in [1,2]:
            te=list("abcd") if f==1 else list("efgh");other=[s for s in self.c.subject_id if s not in te]
            for role,ids in [("test",te),("train",other[:2]),("validation",other[2:])]:
                for s in ids:
                    y=int(self.c.set_index("subject_id").loc[s,"label"])
                    splits.append(dict(repeat=1,fold=f,subject_id=s,role=role,label=y,site="A"))
                    if role=="test":
                        for m in ["baseline","image"]:pred.append(dict(repeat=1,fold=f,subject_id=s,model=m,y=y,site="A",score=.2+.6*y))
        self.s=pd.DataFrame(splits);self.p=pd.DataFrame(pred)
    def check(self,c=None,s=None,p=None):
        return self.validate(self.c if c is None else c,self.s if s is None else s,self.p if p is None else p,repeats=1,folds=2,models=["baseline","image"])
    def test_valid_permuted_predictions_align_by_id(self):
        self.check(p=self.p.sample(frac=1,random_state=9))
    def test_duplicate_prediction_rejected(self):
        with self.assertRaises(ValueError):self.check(p=pd.concat([self.p,self.p.iloc[[0]]]))
    def test_missing_prediction_rejected(self):
        with self.assertRaises(ValueError):self.check(p=self.p.iloc[1:])
    def test_wrong_label_rejected(self):
        p=self.p.copy();p.loc[0,"y"]=1-p.loc[0,"y"]
        with self.assertRaises(ValueError):self.check(p=p)
    def test_subject_role_overlap_rejected(self):
        s=pd.concat([self.s,self.s.query("role == 'test'").iloc[[0]].assign(role="train")])
        with self.assertRaises(ValueError):self.check(s=s)
    def test_wrong_test_membership_rejected(self):
        p=self.p.copy();p.loc[0,"subject_id"]="e"
        with self.assertRaises(ValueError):self.check(p=p)
    def test_unknown_site_or_nonfinite_score_rejected(self):
        for col,value in [("site","unknown"),("score",np.nan)]:
            p=self.p.copy();p.loc[0,col]=value
            with self.assertRaises(ValueError):self.check(p=p)
    def test_fold_average_does_not_pool_incomparable_margins(self):
        p=self.p.copy();p.loc[p.fold.eq(2),"score"]+=100
        fold,repeat,summary=self.aggregate(p)
        np.testing.assert_allclose(summary.mean_auc,1.)
    def test_replay_preserves_original_float32_image_multiplication(self):
        from adhd_fmri_benchmark.evidence import combine_scores
        base=np.array([.623,.427],dtype=np.float64);image=np.array([.71234567,.39876543],dtype=np.float32);alpha=.75
        expected=(1-alpha)*base+alpha*image
        reloaded=image.astype(np.float64)
        np.testing.assert_array_equal(combine_scores(base,reloaded,alpha,image_float32=True),expected)

    def test_within_site_auc_ignores_cross_site_pairs(self):
        from adhd_fmri_benchmark.evidence import within_site_auc
        p=pd.DataFrame({"site":["A","A","B","B"],"y":[0,1,0,1],"score":[.1,.2,.8,.9]})
        self.assertEqual(within_site_auc(p),1.)

if __name__ == "__main__":unittest.main()
