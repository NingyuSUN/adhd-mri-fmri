# User-configured directories

Project-owned code must not contain a developer's personal working directory.
Paths to repository resources are resolved from `__file__`. External data and
output directories are supplied by the user. Relative command-line paths are
relative to the caller's current working directory. No `os.chdir` is required.

From any directory, set `REPO` to your checkout, `SOURCE` to your private analysis
workspace, and `DEST` to a new output directory. For example, in Bash:

```bash
read -r -p "Repository directory: " REPO
read -r -p "Private source workspace: " SOURCE
read -r -p "New output directory: " DEST
python "$REPO/tools/portfolio_quickstart.py" --output-dir "$DEST"
python "$REPO/tools/validate_public_artifacts.py"
```

For fresh fitting, use a different new `DEST` and the locked runtime environment:

```bash
python "$REPO/reproduction/reproduce_v2.py" --source "$SOURCE" --out "$DEST" --workers 1 --limit 1
```

The required private input layout and full workflow are in
[reproduction/README.md](../reproduction/README.md). The source tree's fixed
relative run names identify frozen inputs; they do not identify a personal mount.
The public aggregate package is sufficient for the quickstart, not full refitting.

## Historical inventory helper

The inventory helper requires explicit paths. Set the variables below to your own
locations before running; `T1_SOURCE_PREFIX` is the old data-root prefix recorded
in your input manifest. It is remapped to `DATA_ROOT` with traversal protection.

```bash
python "$REPO/reproduction/legacy/build_multimodal_manifest.py" \
  --data-root "$DATA_ROOT" --source "$SOURCE" --features "$FEATURES" \
  --t1-source-prefix "$T1_SOURCE_PREFIX" \
  --roi-notebook "$ROI_NOTEBOOK" --swin-notebook "$SWIN_NOTEBOOK" \
  --out "$INVENTORY_OUT"
```

Original notebooks are private provenance inputs, not files to add to this repo.
The inventory remains a private output: it contains subject-level records and
resolved local input paths. Export only reviewed aggregate artifacts for publication.

## Snapshot compatibility

This portability change modifies `legacy/build_multimodal_manifest.py` and its
entry in `legacy_manifest.json`. Its imported `norm_id` and `digest` functions
and all nine protocol-listed training sources are unchanged. The manifest change
is intentional and versioned; historical execution manifests are not rewritten.

Existing executions bind the previous manifest hash and must be resumed or
verified using their original snapshot. For the previously published September
execution, the pre-portability source is preserved at commit
`fb7c0de94f64932ba2538612e490175f5a5c0f83`:

```bash
git worktree add ../adhd-historical fb7c0de94f64932ba2538612e490175f5a5c0f83
```

Use that worktree's verifier for those executions. The current verifier continues
to reject a mismatched source manifest; no compatibility bypass was added.
New executions record the new package manifest. Full 66-unit replay has not been
rerun as part of this portability change.

The public-path validator now scans project-owned reproduction code as well as
the existing public roots and uses generic home/mount/drive rules. Vendored
third-party sources retain their original bytes and separate manifest checks.
Generated Python bytecode is not interpreted as public source text.
