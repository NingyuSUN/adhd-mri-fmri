"""Finish one already-running execution; never starts or duplicates training."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
from completion import write_json


def identity(pid):
    proc=Path('/proc')/str(pid)
    try:
        stat=proc.joinpath('stat').read_text().rsplit(') ',1)[1].split()
        if stat[0]=='Z':return None
        return stat[19],proc.joinpath('cmdline').read_bytes().split(b'\0')
    except FileNotFoundError:return None


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--training-pid',type=int,required=True)
    ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--stats-out',type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();me=Path(__file__).resolve().parent
    original=a.source.resolve()/'runs/structural_fusion_v2_20260910'
    if out==original or original in out.parents:raise ValueError('refuse original output path')
    target=identity(a.training_pid)
    if target is not None:
        cmd=target[1]
        if str(out).encode() not in cmd or not any(b'reproduce_v2.py' in x for x in cmd):raise ValueError('PID does not identify requested reproduction')
    state=out/'pipeline_status.json';last=None
    try:
        while target is not None and identity(a.training_pid)==target:
            status=json.loads((out/'reproduction_status.json').read_text())
            current=(status.get('status'),status.get('completed',status.get('units',0)))
            if current!=last:
                write_json(state,dict(status='waiting_for_training_exit',completed=current[1],planned=66,training_pid=a.training_pid,finisher_pid=os.getpid()))
                print('TRAINING',current,flush=True);last=current
            time.sleep(30)
        write_json(state,dict(status='verifying',planned=66,finisher_pid=os.getpid()))
        subprocess.run([sys.executable,str(me/'verify_fresh.py'),'--source',str(a.source.resolve()),'--out',str(out),'--stats-out',str(a.stats_out.resolve())],check=True)
        proof=json.loads((out/'verified_reproduction.json').read_text())
        if proof['status']!='verified_full_feature_level_reproduction' or proof['units']!=66:raise ValueError('missing final proof')
        write_json(state,dict(status='verified_full_feature_level_reproduction',completed=66,planned=66))
        print('PIPELINE VERIFIED 66/66',flush=True)
    except BaseException as exc:
        write_json(state,dict(status='failed',error=repr(exc)))
        raise

if __name__=='__main__':main()
