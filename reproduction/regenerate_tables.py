"""Re-execute original statistics/calibration without editing the frozen implementation."""
from pathlib import Path
import argparse,importlib.util,json,sys
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent


def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/'legacy'/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--reference-run',type=Path)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);reference=a.reference_run or a.run
    original_argv=sys.argv.copy()
    for name in ['analyze_v2_stats','calibration_v2']:
        m=load(name);m.OUT=a.run
        sys.argv=[name,'--out',str(a.out)];m.main()
    sys.argv=original_argv
    for fw in ['cv','loso']:
        pd.read_csv(a.run/fw/'primary/summary.csv').to_csv(a.out/(fw+'_primary_summary.csv'),index=False)
    checks=[]
    for name in ['cv_contrast_stats.csv','loso_contrast_stats.csv','loso_per_site_deltas.csv','calibration.csv','calibration_summary.csv']:
        old=pd.read_csv(reference/'v2_stats'/name);new=pd.read_csv(a.out/name)
        pd.testing.assert_frame_equal(old,new,check_exact=False,rtol=1e-10,atol=1e-12)
        cols=old.select_dtypes(include='number').columns
        diff=np.abs(old[cols].to_numpy()-new[cols].to_numpy())
        checks.append(dict(file=name,rows=len(old),max_numeric_difference=float(np.nanmax(diff)),matched=True))
    old=json.loads((reference/'v2_stats/decision.json').read_text());new=json.loads((a.out/'decision.json').read_text())
    if old!=new:raise ValueError('original decision not reproduced exactly')
    write=dict(status='verified',tables=checks,decision_reproduced_exactly=True,scope='saved_prediction_statistical_recomputation')
    figs=load('figures_v2');fd=a.out/'figures';fd.mkdir()
    figs.f1_forest(a.out,fd);figs.f2_bars(a.out,fd);figs.f3_reliability(a.out,fd)
    (a.out/'recomputation_verification.json').write_text(json.dumps(write,indent=2)+'\n')
    print(json.dumps(write,indent=2))

if __name__=='__main__':main()
