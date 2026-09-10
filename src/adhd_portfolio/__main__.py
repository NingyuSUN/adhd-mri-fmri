"""Command-line entry points; imports for neural models remain optional."""
import argparse,json
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description='ADHD-200 fMRI portfolio: evidence replay, synthetic demo and frozen runtime preflight')
    commands=parser.add_subparsers(dest='command',required=True)
    evidence=commands.add_parser('verify',help='Replay local frozen evidence; export only aggregate metrics')
    evidence.add_argument('--release',type=Path,required=True);evidence.add_argument('--out',type=Path,required=True)
    demo=commands.add_parser('demo',help='Train LR and the frozen MLP on clearly labeled synthetic data')
    demo.add_argument('--out',type=Path,required=True)
    frozen=commands.add_parser('frozen',help='Inspect prerequisites or explicitly execute a frozen stage')
    frozen.add_argument('--runtime-root',type=Path,required=True);frozen.add_argument('--out',type=Path,required=True)
    frozen.add_argument('--stage',choices=['representation','site_motion_increment','demographic_increment'],required=True)
    frozen.add_argument('--parent',type=Path);frozen.add_argument('--prepare-only',action='store_true');frozen.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if args.command=='verify':
        from .evidence import replay_release
        r=replay_release(args.release,args.out);print(json.dumps({'status':r['status'],'runs':r['runs'],'validation_alpha_checks':r['validation_alpha_checks'],'out':str(args.out)},indent=2))
    elif args.command=='demo':
        from .smoke import run_demo
        print(json.dumps(run_demo(args.out),indent=2))
    else:
        from .frozen import run_stage
        print(json.dumps(run_stage(args),indent=2))

if __name__=='__main__':main()
