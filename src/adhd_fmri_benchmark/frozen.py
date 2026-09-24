"""Load byte-preserved scientific code and relocate input paths in memory only."""
from pathlib import Path
import importlib
import importlib.metadata
import json
import os
import sys
from .evidence import require,sha256,RUNS

SOURCE=Path(__file__).resolve().parent/'frozen_v1'
MODULES=['run_paired','build_multimodal_manifest','run_functional_fusion','run_connectivity','temporal_models','run_temporal','run_tcn_fc_completion','run_connectome_representations','refine_tangent_reference','run_repeated_connectome','run_incremental_imaging','run_demographic_increment']
ENTRY={'representation':'run_repeated_connectome','site_motion_increment':'run_incremental_imaging','demographic_increment':'run_demographic_increment'}
EXPECTED={'numpy':'2.5.3','scipy':'1.18.1','pandas':'3.0.5','scikit-learn':'1.9.0','torch':'2.14.0+cpu','joblib':'1.6.0','nilearn':'0.12.1','nibabel':'5.3.2','packaging':'25.0','threadpoolctl':'3.6.0'}
ORIGINAL_PATHS={}
NUMERICAL_SHA='a50da2b8883df37dcefd1b7bb617aa200d38bec117cb5ed1c26a081dc8789900'

def load_modules():
    inventory=json.loads((SOURCE/'sources.json').read_text(encoding="utf-8"))
    require({r['file'] for r in inventory}=={n+'.py' for n in MODULES},'Scientific module inventory mismatch')
    for record in inventory:require(sha256(SOURCE/record['file'])==record['sha256'],'Scientific source modified: '+record['file'])
    vendor=os.environ.get('ADHD_NILEARN_VENDOR')
    if vendor:
        require(Path(vendor).is_dir(),'ADHD_NILEARN_VENDOR is not a directory')
        sys.path.insert(0,str(Path(vendor).resolve()))
    sys.path.insert(0,str(SOURCE))
    for name in MODULES:
        if name in sys.modules:require(Path(sys.modules[name].__file__).resolve()==(SOURCE/(name+'.py')).resolve(),'Conflicting imported scientific module: '+name)
    modules={n:importlib.import_module(n) for n in MODULES}
    for name,module in modules.items():
        if name not in ORIGINAL_PATHS:
            ORIGINAL_PATHS[name]={key:value for key,value in vars(module).items() if isinstance(value,Path) and value.is_relative_to(SOURCE)}
    return modules

def environment():
    import nilearn.connectome.connectivity_matrices as matrices
    versions={n:importlib.metadata.version(n) for n in EXPECTED}
    digest=sha256(matrices.__file__)
    return dict(python=sys.version.split()[0],versions=versions,version_mismatches={n:{'expected':v,'actual':versions[n]} for n,v in EXPECTED.items() if versions[n]!=v},numerical_source_sha256=digest,numerical_source_matches=digest==NUMERICAL_SHA)

def relocate(modules,runtime):
    runtime=Path(runtime).resolve()
    for name,module in modules.items():
        for key,value in ORIGINAL_PATHS[name].items():
            # BASE remains code location: frozen entry points copy source from it.
            if key!='BASE' and isinstance(value,Path) and value.is_relative_to(SOURCE):
                setattr(module,key,runtime/value.relative_to(SOURCE))

def run_stage(args):
    runtime=args.runtime_root.resolve();out=args.out.resolve()
    require(runtime.is_dir(),'Runtime root does not exist')
    require(not out.exists(),'Refusing an existing output directory')
    require(not out.is_relative_to(runtime),'Output must be outside the source runtime')
    require(not out.is_relative_to(SOURCE.parent),'Output cannot be inside the package')
    require(not (args.prepare_only and args.stage!='representation'),'Prepare-only applies to representation stage')
    modules=load_modules();relocate(modules,runtime);module=modules[ENTRY[args.stage]]
    parent=args.parent.resolve() if args.parent else None
    if parent:
        require(args.stage!='representation','Representation stage does not accept a parent override')
        module.PARENT=parent
    input_files=[]
    if args.stage=='representation':input_files=[module.OLD/'cohort.csv']
    else:input_files=[module.PARENT/n for n in ['cohort.csv','splits.csv','predictions.csv','status.json']]
    if args.stage in ['representation','site_motion_increment'] and not args.prepare_only:
        loader=modules['run_tcn_fc_completion']
        input_files.extend(loader.REFERENCE/n for n in ['cohort.csv','splits.csv','verification.json'])
        input_files.extend(loader.CACHE/n for n in ['cohort.csv','timeseries.npz','verification.json'])
        input_files.extend(loader.FEATURES/n for n in ['features.npz','verification.json'])
    if args.stage=='demographic_increment':
        input_files.extend(module.PARENT/f'repeat{r}_fold{f}_validation.csv' for r in range(1,6) for f in range(1,4))
    if args.stage=='site_motion_increment':
        for r in range(1,6):
            for f in range(1,4):
                folder=module.PARENT/f'repeat{r}_fold{f}'
                input_files.extend(folder/n for n in ['reference.joblib','tangent_transform.joblib','controls.joblib','site_motion_lr.joblib','tangent_lr.joblib'])
                input_files.extend(folder/f'fold{f}_tangent_mlp_seed{seed}.pt' for seed in [1200+f,2200+f,3200+f])
    missing=[str(p) for p in input_files if not p.is_file()];env=environment()
    report={'stage':args.stage,'mode':'prepare-only' if args.prepare_only else 'execute' if args.execute else 'preflight','missing_inputs':missing,'environment':env,'out':str(out),'source_files':len(MODULES),'scope':'Path relocation only; frozen model definitions, splits, selection and training settings unchanged. Historical full training has not been rerun by this wrapper unless explicitly executed.'}
    if not args.execute and not args.prepare_only:return report
    require(not missing,'Missing required data; run preflight and inspect missing_inputs')
    require(not env['version_mismatches'] and env['numerical_source_matches'],'Environment differs from recorded numerical runtime')
    out.parent.mkdir(parents=True,exist_ok=True)
    if args.stage=='demographic_increment':module.OUT=out;argv=[module.__file__]
    else:argv=[module.__file__,'--out',str(out)]
    if args.prepare_only:argv.append('--prepare-only')
    previous=sys.argv
    try:sys.argv=argv;module.main()
    finally:sys.argv=previous
    (out/'portable_execution.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    report['completed']=True
    return report
