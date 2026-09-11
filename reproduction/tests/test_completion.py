import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import pytest
from integrity import digest
from completion import publish_unit, verify_unit, finalize_report


def test_resume_requires_last_marker_and_detects_comparison_mutation(tmp_path):
    (tmp_path/'prediction.csv').write_text('toy result')
    (tmp_path/'complete.json').write_text(json.dumps({'files':{'prediction.csv':digest(tmp_path/'prediction.csv')}}))
    (tmp_path/'comparison.json').write_text('{}')
    with pytest.raises(FileNotFoundError):verify_unit(tmp_path)
    publish_unit(tmp_path)
    verify_unit(tmp_path)
    (tmp_path/'comparison.json').write_text('{"tampered":true}')
    with pytest.raises(ValueError):verify_unit(tmp_path)


def test_failed_summary_cannot_leave_terminal_success(tmp_path):
    def fail():raise RuntimeError('summary failed')
    (tmp_path/'reproduction_report.json').write_text('{"status":"complete_matched"}')
    with pytest.raises(RuntimeError):finalize_report(tmp_path,{'status':'complete_matched'},fail)
    assert not (tmp_path/'reproduction_report.json').exists()
    assert json.loads((tmp_path/'reproduction_status.json').read_text())['status']=='failed'


def test_terminal_report_is_published_only_after_summary(tmp_path):
    def summarize():
        assert not (tmp_path/'reproduction_report.json').exists()
        (tmp_path/'summary.csv').write_text('verified summary')
    finalize_report(tmp_path,{'status':'complete_matched'},summarize)
    assert (tmp_path/'summary.csv').exists()
    assert json.loads((tmp_path/'reproduction_report.json').read_text())['status']=='complete_matched'


def test_final_gate_clears_stale_success_when_preflight_fails(tmp_path,monkeypatch):
    import verify_fresh
    source=tmp_path/'original';source.mkdir();out=tmp_path/'fresh';out.mkdir()
    (out/'verified_reproduction.json').write_text('{"status":"verified"}')
    monkeypatch.setattr(sys,'argv',['verify_fresh','--source',str(source),'--out',str(out),'--stats-out',str(tmp_path/'stats')])
    def fail(*args):raise ValueError('changed metadata')
    monkeypatch.setattr(verify_fresh,'preflight',fail)
    with pytest.raises(ValueError,match='changed metadata'):verify_fresh.main()
    assert not (out/'verified_reproduction.json').exists()
    assert json.loads((out/'verification_status.json').read_text())['status']=='failed'


def test_final_gate_rejects_statistics_writes_inside_source(tmp_path,monkeypatch):
    import verify_fresh
    source=tmp_path/'original';source.mkdir();out=tmp_path/'fresh';out.mkdir()
    monkeypatch.setattr(sys,'argv',['verify_fresh','--source',str(source),'--out',str(out),'--stats-out',str(source/'newstats')])
    monkeypatch.setattr(verify_fresh,'preflight',lambda *args: {})
    with pytest.raises(ValueError,match='statistics output'):verify_fresh.main()
    assert not (source/'newstats').exists()


def test_resume_rejects_a_completed_unit_copied_into_another_job(tmp_path):
    (tmp_path/'complete.json').write_text(json.dumps({'files':{},'protocol_sha256':'protocol'}))
    (tmp_path/'comparison.json').write_text(json.dumps({'framework':'cv','cohort':'primary','unit':'repeat1_fold1'}))
    publish_unit(tmp_path)
    with pytest.raises(ValueError,match='job identity'):verify_unit(tmp_path,expected_job=('cv','primary','repeat2_fold1'),protocol_hash='protocol')


def test_finisher_cannot_write_into_original_run(tmp_path,monkeypatch):
    import finish_execution
    source=tmp_path/'source';out=source/'runs/structural_fusion_v2_20260910';out.mkdir(parents=True)
    monkeypatch.setattr(sys,'argv',['finish_execution','--training-pid','999999999','--source',str(source),'--out',str(out),'--stats-out',str(tmp_path/'stats')])
    with pytest.raises(ValueError,match='original output'):finish_execution.main()
    assert not list(out.iterdir())
