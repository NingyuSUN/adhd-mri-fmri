import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import numpy as np
import pandas as pd
import pytest
from statistics_audit import paired_scores, interval_evidence, decompose_shift, auc


def test_pairing_uses_subject_ids_not_row_order():
    p=pd.DataFrame({'subject_id':['a','b','b','a'],'site':['X']*4,'y':[0,1,1,0],
                    'model':['candidate','candidate','reference','reference'],'score':[.1,.9,.2,.8]})
    w=paired_scores(p,'candidate','reference')
    assert auc(w.y,w.candidate)-auc(w.y,w.reference)==1.0


def test_pairing_rejects_missing_subject_in_one_model():
    p=pd.DataFrame({'subject_id':['a','b','a'],'site':['X']*3,'y':[0,1,0],
                    'model':['candidate','candidate','reference'],'score':[.1,.9,.8]})
    with pytest.raises(ValueError,match='subject'):
        paired_scores(p,'candidate','reference')


def test_duplicate_or_mismatched_labels_fail():
    p=pd.DataFrame({'subject_id':['a','b','a','b'],'site':['X']*4,'y':[0,1,1,1],
                    'model':['candidate','candidate','reference','reference'],'score':[.1,.9,.2,.8]})
    with pytest.raises(ValueError,match='label'):
        paired_scores(p,'candidate','reference')


def test_sign_is_distinct_from_materiality():
    d=interval_evidence(.009,.046)
    assert d['positive_supported']
    assert not d['meaningful_positive_supported']
    assert not d['equivalence_supported']
    assert interval_evidence(.021,.05)['meaningful_positive_supported']
    assert interval_evidence(-.01,.01)['equivalence_supported']


def test_decomposition_reconstructs_total_with_different_evaluation_sets():
    # Full A=.1, full B=-.2; common A=.05, common B=-.1.
    r=decompose_shift(.1,-.2,.05,-.1)
    assert r['total_shift']==pytest.approx(-.3)
    assert r['common_subject_model_shift']==pytest.approx(-.15)
    assert r['evaluation_composition_shift']==pytest.approx(-.15)
    assert abs(r['identity_residual'])<1e-14


def test_auc_gives_half_credit_to_cross_class_ties():
    assert auc(np.array([0,1]),np.array([.5,.5]))==.5
    assert auc(np.array([0,0,1,1]),np.array([.1,.5,.5,.9]))==.875


def test_conditional_bootstrap_perfect_paired_difference():
    from statistics_audit import conditional_boot
    w=pd.DataFrame({'subject_id':['a','b'],'site':['X','X'],'y':[0,1],'candidate':[.1,.9],'reference':[.9,.1]})
    assert conditional_boot(w,pd.Series({'X':1.}),n_boot=20)==[1.,1.]


def test_symmetric_two_factor_decomposition_splits_interaction():
    from statistics_audit import shapley_two_factor
    r=shapley_two_factor(0.,.2,.1,.5)
    assert r['prediction_contribution']==pytest.approx(.2)
    assert r['fusion_weight_contribution']==pytest.approx(.3)
    assert r['identity_residual']==pytest.approx(0.)


def test_alpha_selection_ties_prefer_less_added_modality():
    from statistics_audit import select_alpha
    y=np.array([0,1]);same=np.array([.1,.9])
    assert select_alpha(y,same,same)==0.
    assert select_alpha(y,np.array([.9,.1]),same)==.75
