import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import pandas as pd
import pytest
from integrity import compare_predictions, verify_manifest


def test_compare_preserves_identity_and_rejects_missing_rows():
    a=pd.DataFrame({'subject_id':['a','b'],'model':['m','m'],'site':['X','X'],'y':[0,1],'score':[.1,.9]})
    assert compare_predictions(a,a.iloc[::-1])['max_abs_score_difference']==0
    with pytest.raises(ValueError):compare_predictions(a,a.iloc[:1])


def test_compare_rejects_label_corruption():
    a=pd.DataFrame({'subject_id':['a','b'],'model':['m','m'],'site':['X','X'],'y':[0,1],'score':[.1,.9]})
    b=a.copy();b.loc[0,'y']=1
    with pytest.raises(ValueError):compare_predictions(a,b)


def test_manifest_detects_modified_file(tmp_path):
    (tmp_path/'x').write_text('abc')
    hashes={'x':'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'}
    assert verify_manifest(tmp_path,hashes)==1
    (tmp_path/'x').write_text('abd')
    with pytest.raises(ValueError):verify_manifest(tmp_path,hashes)
