"""Publish verifiable completion only after all dependent work has succeeded."""
import json
from integrity import digest,verify_manifest


def write_json(path,value):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temp.replace(path)


def publish_unit(folder):
    """Caller has closed all output streams and validated the comparison."""
    marker=json.loads((folder/'complete.json').read_text())
    marker['files']={p.name:digest(p) for p in folder.iterdir()
                     if p.is_file() and p.name not in {'complete.json','reproduction_complete.json'}}
    write_json(folder/'complete.json',marker)
    write_json(folder/'reproduction_complete.json',dict(schema=1,files={
        name:digest(folder/name) for name in ['complete.json','comparison.json']}))


def verify_unit(folder,expected_job=None,protocol_hash=None):
    marker=json.loads((folder/'reproduction_complete.json').read_text())
    if marker.get('schema')!=1 or set(marker['files'])!={'complete.json','comparison.json'}:
        raise ValueError('invalid reproduction completion marker')
    verify_manifest(folder,marker['files'])
    complete=json.loads((folder/'complete.json').read_text())
    verify_manifest(folder,complete['files'])
    result=json.loads((folder/'comparison.json').read_text())
    if expected_job is not None and tuple(result[k] for k in ['framework','cohort','unit'])!=tuple(expected_job):raise ValueError('completed job identity mismatch')
    if protocol_hash is not None and complete['protocol_sha256']!=protocol_hash:raise ValueError('completed protocol mismatch')
    return result


def finalize_report(folder,report,summarize):
    terminal=folder/'reproduction_report.json'
    terminal.unlink(missing_ok=True)
    try:
        summarize()
        write_json(terminal,report)
        write_json(folder/'reproduction_status.json',{k:v for k,v in report.items() if k!='results'})
    except BaseException as exc:
        terminal.unlink(missing_ok=True)
        write_json(folder/'reproduction_status.json',dict(status='failed',error=repr(exc)))
        raise
