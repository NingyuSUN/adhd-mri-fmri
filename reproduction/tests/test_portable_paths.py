import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "inventory", ROOT / "reproduction/legacy/build_multimodal_manifest.py"
)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


def test_inventory_requires_user_directories():
    with pytest.raises(SystemExit) as error:
        inventory.parse_args([])
    assert error.value.code == 2


def test_inventory_paths_follow_user_configuration(tmp_path):
    options = ["data-root", "source", "features", "roi-notebook", "swin-notebook", "out"]
    arguments = [value for name in options for value in ("--" + name, str(tmp_path / name))]
    args = inventory.parse_args(arguments + ["--t1-source-prefix", "original-data"])
    for name in options:
        assert getattr(args, name.replace("-", "_")) == tmp_path / name


def test_manifest_paths_remap_to_user_data_root(tmp_path):
    assert inventory.local_t1("original-data/site/image.nii.gz", tmp_path, "original-data") == tmp_path / "site/image.nii.gz"
    assert inventory.local_t1("original-data\\site\\image.nii.gz", tmp_path, "original-data") == tmp_path / "site/image.nii.gz"


@pytest.mark.parametrize("path", ["wrong/site/image.nii.gz", "original-data/../outside", "original-data//outside"])
def test_manifest_remapping_rejects_wrong_prefix_and_escape(tmp_path, path):
    with pytest.raises(ValueError):
        inventory.local_t1(path, tmp_path, "original-data")


def test_manifest_remapping_rejects_symlink_escape(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    try:
        (data / "escape").symlink_to(tmp_path, target_is_directory=True)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows account cannot create symlinks; this invariant runs in Linux CI")
        raise
    with pytest.raises(ValueError):
        inventory.local_t1("original-data/escape/file", data, "original-data")


def test_public_commands_work_from_an_unrelated_directory(tmp_path):
    for script, arguments in [
        ("portfolio_quickstart.py", ["--output-dir", str(tmp_path / "report")]),
        ("validate_public_artifacts.py", []),
    ]:
        subprocess.run([sys.executable, str(ROOT / "tools" / script), *arguments], cwd=tmp_path, check=True, capture_output=True, text=True)
    assert (tmp_path / "report/summary.json").is_file()
