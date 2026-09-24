import importlib.util
import unittest
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

class ModelInterfaces(unittest.TestCase):
    def test_frozen_loader_exists(self):
        self.assertIsNotNone(importlib.util.find_spec('adhd_fmri_benchmark.frozen'),'Frozen model loader is missing')

class ModelBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec('adhd_fmri_benchmark.frozen') is None:raise unittest.SkipTest('implementation not yet present')
        from adhd_fmri_benchmark.frozen import load_modules
        cls.modules=load_modules()
    def test_feature_selection_and_scaling_ignore_held_out_values_and_labels(self):
        rng=np.random.default_rng(2);x=rng.normal(size=(40,12));y=np.arange(40)%2;tr=np.arange(24)
        fn=self.modules['run_connectome_representations'].select_features
        a,ia,sa=fn(x,y,tr,k=5);other=x.copy();other[24:]*=1000;yy=y.copy();yy[24:]=1-yy[24:]
        b,ib,sb=fn(other,yy,tr,k=5)
        np.testing.assert_array_equal(ia,ib);np.testing.assert_array_equal(a[tr],b[tr]);np.testing.assert_array_equal(sa.mean_,sb.mean_)
    def test_covariate_preprocessing_ignores_held_out_extremes(self):
        rng=np.random.default_rng(4);c=pd.DataFrame({'subject_id':[f's{i}' for i in range(30)],'site':['A','B']*15,'mean_fd':rng.normal(size=30),'pct_fd_gt_0p2':rng.normal(size=30),'mean_dvars':rng.normal(size=30),'participant_age':rng.uniform(8,18,30),'participant_sex_male':np.arange(30)%2})
        tr=np.arange(18);other=c.copy();other.loc[18:,'site']='UNSEEN';other.loc[18:,'mean_fd']=1e10;other.loc[18:,'participant_age']=100
        for name,fn in [('controls',self.modules['run_repeated_connectome'].controls),('demographics',self.modules['run_demographic_increment'].demographic)]:
            a,fa=fn(c,tr);b,fb=fn(other,tr)
            if isinstance(a,dict):
                for k in a:np.testing.assert_array_equal(a[k][tr],b[k][tr])
            else:np.testing.assert_array_equal(a[tr],b[tr])
            self.assertEqual(fa['fit_ids'],c.subject_id.iloc[tr].tolist());self.assertEqual(fa['fit_ids'],fb['fit_ids'])
    def test_tangent_reference_does_not_change_when_transforming_held_out_series(self):
        fn=self.modules['run_connectome_representations'].tangent_features
        rng=np.random.default_rng(9);data=[rng.normal(size=(30,4)) for _ in range(12)];tr=np.arange(8)
        a,ma,_=fn(data,tr);data2=data[:8]+[d*10 for d in data[8:]];b,mb,_=fn(data2,tr)
        np.testing.assert_allclose(ma.mean_,mb.mean_,rtol=0,atol=1e-12);np.testing.assert_allclose(a[tr],b[tr],rtol=0,atol=1e-7)
    def test_runtime_relocation_is_reset_between_invocations(self):
        from adhd_fmri_benchmark.frozen import relocate,SOURCE
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'one';b=Path(temp)/'two'
            relocate(self.modules,a);relocate(self.modules,b)
            self.assertTrue(self.modules['run_repeated_connectome'].OLD.is_relative_to(b))
            self.assertEqual(self.modules['run_repeated_connectome'].BASE,SOURCE)

    def test_existing_output_is_refused_before_loading_or_writing(self):
        from adhd_fmri_benchmark.frozen import run_stage
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            runtime=Path(temp)/'runtime';runtime.mkdir();out=Path(temp)/'out';out.mkdir()
            marker=out/'keep.txt';marker.write_text('keep')
            args=SimpleNamespace(runtime_root=runtime,out=out,stage='representation',parent=None,prepare_only=False,execute=False)
            with self.assertRaises(ValueError):run_stage(args)
            self.assertEqual(marker.read_text(),'keep')

    def test_alpha_ties_choose_zero_image_weight(self):
        from adhd_fmri_benchmark.evidence import select_alpha
        y=np.array([0,1,0,1]);p=np.array([.1,.9,.2,.8])
        self.assertEqual(select_alpha(y,p,p)[0],0.)
        self.assertEqual(self.modules['run_incremental_imaging'].choose_alpha(y,p,p)[0],0.)
    def test_locked_partitions_cover_each_subject_once_per_repeat(self):
        c=pd.DataFrame({'subject_id':[f's{i}' for i in range(378)],'site':['A']*189+['B']*189,'label':np.arange(378)%2})
        parts=list(self.modules['run_repeated_connectome'].partitions(c));self.assertEqual(len(parts),15)
        for r in range(1,6):
            tests=[]
            for rr,fold,tr,va,te in parts:
                if rr!=r:continue
                self.assertEqual([len(tr),len(va),len(te)],[201,51,126]);self.assertFalse(set(tr)&set(te));tests.extend(te)
            self.assertEqual(sorted(tests),list(range(378)))

if __name__=='__main__':unittest.main()
