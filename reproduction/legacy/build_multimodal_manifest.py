"""Audit existing sMRI/fMRI assets; write local inventory only. No training."""
from pathlib import Path
import hashlib
import json
import re
import argparse
import faulthandler
import numpy as np
import pandas as pd



def norm_id(value):
    s = str(value).strip()
    match = re.fullmatch(r'(?:sub-)?(\d+)(?:\.0)?', s)
    if not match:
        raise ValueError(f'Unrecognized ID: {value!r}')
    return 'sub-' + str(int(match[1])).zfill(7)


def sex_code(value):
    return {'female': 0, 'male': 1, '0': 0, '0.0': 0, '1': 1, '1.0': 1}.get(str(value).strip().lower(), np.nan)


def label_code(value):
    s = str(value).strip().lower()
    if s in ('0', '0.0', 'td', 'control', 'typically developing children'):
        return 0
    if s in ('1', '2', '3', '1.0', '2.0', '3.0') or s.startswith('adhd'):
        return 1
    return np.nan


def qc_pass(value):
    return str(value).strip().lower() in ('pass', '1', '1.0', 'true', 't', 'yes', 'y')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def table(path, id_col, label_col=None):
    df = pd.read_csv(path, dtype={id_col: str})
    df['raw_id'] = df[id_col].astype(str)
    df['subject_id'] = df[id_col].map(norm_id)
    if label_col:
        df['binary_label'] = pd.to_numeric(df[label_col], errors='raise').astype(int)
        assert df.binary_label.isin([0, 1]).all(), path
    value_columns = list(df.columns)
    df['source_row'] = np.arange(len(df))
    groups = []
    for _, group in df.groupby(['site', 'subject_id'], sort=False):
        assert len(group[value_columns].drop_duplicates()) == 1, f'Conflicting duplicate identity: {path}'
        record = group.iloc[0].copy()
        record['source_rows'] = json.dumps(group.source_row.tolist())
        record['source_count'] = len(group)
        groups.append(record)
    df = pd.DataFrame(groups)
    return df.set_index(['site', 'subject_id'], drop=False)


def local_t1(path, data_root, source_prefix):
    """Remap a manifest path using a user-supplied original data prefix."""
    prefix = source_prefix.replace("\\", "/").rstrip("/") + "/"
    original = str(path).replace("\\", "/")
    if not original.startswith(prefix):
        raise ValueError("T1 path does not match --t1-source-prefix")
    relative = original[len(prefix):]
    if not relative or any(part in {"", ".."} or ":" in part for part in relative.split("/")):
        raise ValueError("T1 path must stay within --data-root")
    root = Path(data_root).expanduser().resolve()
    mapped = (root / relative).resolve()
    if not mapped.is_relative_to(root):
        raise ValueError("T1 path must stay within --data-root")
    return mapped


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True, help="Local ADHD-200 data directory")
    parser.add_argument("--source", type=Path, required=True, help="Private workspace containing runs/")
    parser.add_argument("--features", type=Path, required=True, help="Feature directory containing cohort.csv")
    parser.add_argument("--t1-source-prefix", required=True, help="Original data-root prefix recorded in the T1 manifest")
    parser.add_argument("--roi-notebook", type=Path, required=True, help="Private original ROI notebook for provenance")
    parser.add_argument("--swin-notebook", type=Path, required=True, help="Private original Swin notebook for provenance")
    parser.add_argument("--out", type=Path, required=True, help="New inventory output directory")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    data_root = args.data_root.expanduser().resolve()
    source = args.source.expanduser().resolve()
    features = args.features.expanduser().resolve()
    out = args.out.expanduser().resolve()
    faulthandler.dump_traceback_later(90, repeat=True)
    out.mkdir(parents=True, exist_ok=False)
    source_files = {
        'strict_structural_manifest': data_root / 'manifest_all_sitefirst_strictpass_noBrown.csv',
        'older_structural_manifest': data_root / 'manifest_all.csv',
        'roi_metadata': data_root / 'combat_roi_metadata_clean.csv',
        'roi_features': data_root / 'combat_roi_features_clean.csv',
        'fmri_all': data_root / 'fmri/strict_loso_benchmark/locked_cohort_all_445.csv',
        'fmri_primary': features / 'cohort.csv',
        'smri_pixel_cache': data_root / 'transformer_first_round/triplanar_axial_224_uint8.npz',
        'roi_notebook': args.roi_notebook.expanduser().resolve(),
        'swin_notebook': args.swin_notebook.expanduser().resolve(),
    }
    structural = table(source_files['strict_structural_manifest'], 'sub_id', 'y')
    old = table(source_files['older_structural_manifest'], 'sub_id', 'y')
    roi = table(source_files['roi_metadata'], 'subject_id', 'y')
    roi['roi_source_row'] = roi.source_row
    x_roi = pd.read_csv(source_files['roi_features'])
    assert int(roi.source_count.sum()) == len(x_roi) and x_roi.shape[1] == 20
    assert np.isfinite(x_roi.to_numpy(dtype=float)).all()
    for _, record in roi.iterrows():
        indices = json.loads(record.source_rows)
        assert np.array_equal(x_roi.iloc[indices].to_numpy(), np.repeat(x_roi.iloc[[indices[0]]].to_numpy(), len(indices), axis=0))
    x_roi = x_roi.iloc[roi.roi_source_row.to_numpy(dtype=int)].reset_index(drop=True)
    fmri = table(source_files['fmri_all'], 'subject_id', 'label')
    primary = table(source_files['fmri_primary'], 'subject_id', 'label')
    assert set(primary.index).issubset(set(fmri.index))
    # Read safe string IDs, not object pickle. Images are bounded ~139 MB uint8.
    with np.load(source_files['smri_pixel_cache'], allow_pickle=False) as z:
        pixel_raw_ids = z['sub_id'].astype(str)
        pixels = z['images']
    assert pixels.shape == (len(pixel_raw_ids), 3, 224, 224) and pixels.dtype == np.uint8
    pixel_ids = [norm_id(s) for s in pixel_raw_ids]
    pixel_lookup = {}
    for i, sid in enumerate(pixel_ids):
        pixel_lookup.setdefault(sid, i)
    pixel_nonconstant = np.ptp(pixels.reshape(len(pixels), -1), axis=1) > 0
    pixel_hashes = [hashlib.sha256(im.tobytes()).hexdigest() for im in pixels]
    pixel_table = pd.DataFrame({'subject_id': pixel_ids, 'sha256': pixel_hashes})
    assert (pixel_table.groupby('subject_id').sha256.nunique() == 1).all()
    hash_n_subjects = pixel_table.groupby('sha256').subject_id.nunique()
    repeated_pixels = pixel_table.sha256.map(hash_n_subjects).gt(1).to_numpy()
    del pixels
    assert structural.subject_id.nunique() == len(structural), 'ID crosses structural sites'
    assert set(pixel_ids).issubset(set(structural.subject_id))
    participants = []
    for site_dir in sorted((data_root / 'RawDataBIDS').iterdir()):
        path = site_dir / 'participants.tsv'
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path, sep='\t', dtype=str)
            encoding = 'utf-8'
        except UnicodeDecodeError:
            df = pd.read_csv(path, sep='\t', dtype=str, encoding='latin1')
            encoding = 'latin1'
        source_files['participants_' + site_dir.name] = path
        for _, r in df.iterrows():
            participants.append({
                'site': site_dir.name, 'subject_id': norm_id(r.participant_id),
                'participant_raw_id': r.participant_id,
                'participant_label': label_code(r.get('dx')),
                'participant_age': pd.to_numeric(r.get('age'), errors='coerce'),
                'participant_sex_male': sex_code(r.get('gender', r.get('sex'))),
                'qc_anat_raw': r.get('qc_anatomical_1', r.get('qc_s1_anat')),
                'qc_rest_raw': r.get('qc_rest_1', r.get('qc_s1_rest_1')),
                'source_disclaimer': r.get('disclaimer', ''), 'participant_encoding': encoding,
            })
    ptable = pd.DataFrame(participants)
    relevant = [c for c in ptable if c != 'participant_raw_id']
    assert all(len(g[relevant].drop_duplicates()) == 1 for _, g in ptable.groupby(['site', 'subject_id']))
    ptable = ptable.drop_duplicates(['site', 'subject_id'])
    ptable = ptable.set_index(['site', 'subject_id'], drop=False)
    rows, conflicts = [], []
    keys = sorted(set(structural.index) | set(fmri.index) | set(roi.index))
    print('Source identities checked; checking', len(keys), 'subject assets.', flush=True)
    for key_number, key in enumerate(keys):
        if key_number % 100 == 0:
            print('Asset inventory', key_number, '/', len(keys), flush=True)
        site, sid = key
        s = structural.loc[key] if key in structural.index else None
        f = fmri.loc[key] if key in fmri.index else None
        r = roi.loc[key] if key in roi.index else None
        p = ptable.loc[key] if key in ptable.index else None
        pri = primary.loc[key] if key in primary.index else None
        rec = {'site': site, 'subject_id': sid, 'in_structural_strict_manifest': s is not None,
               'in_older_419_manifest': key in old.index, 'in_fmri_445': f is not None,
               'in_historical_fmri_409': pri is not None, 'has_roi_metadata': r is not None}
        for name, obj in [('structural', s), ('fmri', f), ('roi', r)]:
            rec[name + '_source_rows'] = obj.source_rows if obj is not None else '[]'
            rec[name + '_source_count'] = int(obj.source_count) if obj is not None else 0
            rec[name + '_raw_id'] = obj.raw_id if obj is not None else ''
            rec[name + '_label'] = obj.binary_label if obj is not None else np.nan
            rec[name + '_age'] = obj.age if obj is not None else np.nan
            rec[name + '_sex_male'] = sex_code(obj.sex) if obj is not None else np.nan
        if p is not None:
            rec.update({c: p[c] for c in p.index if c not in ('site', 'subject_id')})
        else:
            rec.update({'qc_anat_raw': '', 'qc_rest_raw': '', 'participant_label': np.nan,
                        'participant_age': np.nan, 'participant_sex_male': np.nan})
        rec['anatomical_metadata_qc_pass'] = qc_pass(rec['qc_anat_raw'])
        rec['rest_metadata_qc_pass'] = qc_pass(rec['qc_rest_raw'])
        rec['t1_path_original'] = s.t1_path if s is not None else ''
        tp = local_t1(s.t1_path, data_root, args.t1_source_prefix) if s is not None else None
        rec['t1_path_local'] = str(tp) if tp else ''
        # Mounted Drive may block indefinitely on online-only raw T1 stat calls.
        # Explicitly leave raw-file availability unknown; inspect keyed pixel cache instead.
        rec['t1_file_exists'] = None
        rec['t1_bytes'] = None
        rec['t1_availability_status'] = 'not_checked_cloud_stat_latency' if tp else 'not_in_strict_manifest'
        rec['raw_t1_readability_checked'] = False
        rec['roi_source_row'] = int(r.roi_source_row) if r is not None else -1
        rec['roi_pairing_evidence'] = 'notebook_coexport_same_mask_not_recomputed' if r is not None else ''
        rec['pixel_source_row'] = pixel_lookup.get(sid, -1)
        pi = rec['pixel_source_row']
        rec['has_keyed_smri_pixels'] = pi >= 0
        rec['smri_pixels_nonconstant'] = bool(pixel_nonconstant[pi]) if pi >= 0 else False
        rec['smri_pixels_exact_duplicate'] = bool(repeated_pixels[pi]) if pi >= 0 else False
        rec['smri_pixels_sha256'] = pixel_hashes[pi] if pi >= 0 else ''
        fp = data_root / 'fmri/brainlm_a424/timeseries_raw' / (str(f.raw_id) + '.npy') if f is not None else None
        rec['fmri_timeseries_path'] = str(fp) if fp else ''
        rec['fmri_timeseries_exists'] = fp.is_file() if fp else False
        for c in ['mean_fd', 'max_fd', 'pct_fd_gt_0p2', 'mean_dvars', 'n_volumes', 'motion_status']:
            rec[c] = pri[c] if pri is not None else np.nan
        rec['label_conflict'] = False
        rec['age_conflict'] = False
        rec['sex_conflict'] = False
        for attribute, names, tolerance in [
                ('label', ['structural_label', 'fmri_label', 'roi_label', 'participant_label'], 0),
                ('age', ['structural_age', 'fmri_age', 'roi_age', 'participant_age'], .011),
                ('sex', ['structural_sex_male', 'fmri_sex_male', 'roi_sex_male', 'participant_sex_male'], 0)]:
            observed = {n: float(rec[n]) for n in names if pd.notna(rec.get(n))}
            if observed and max(observed.values()) - min(observed.values()) > tolerance:
                rec[attribute + '_conflict'] = True
                conflicts.append({'site': site, 'subject_id': sid, 'attribute': attribute,
                                  'values_json': json.dumps(observed)})
        rec['label'] = next((rec[c] for c in ['structural_label', 'fmri_label', 'roi_label'] if pd.notna(rec[c])), np.nan)
        if rec['label_conflict']:
            rec['label'] = np.nan  # Never silently resolve disputed outcomes.
        rec['paired_assets_445'] = bool(s is not None and f is not None and not rec['label_conflict']
            and rec['anatomical_metadata_qc_pass']
            and rec['has_keyed_smri_pixels'] and rec['smri_pixels_nonconstant']
            and not rec['smri_pixels_exact_duplicate'] and rec['fmri_timeseries_exists'])
        rec['paired_assets_historical409'] = rec['paired_assets_445'] and pri is not None
        rec['paired_clean_metadata409'] = rec['paired_assets_historical409'] and not rec['age_conflict'] and not rec['sex_conflict']
        rec['paired_rest_qc409'] = rec['paired_clean_metadata409'] and rec['rest_metadata_qc_pass']
        rows.append(rec)
    manifest = pd.DataFrame(rows)
    assert not manifest.duplicated(['site', 'subject_id']).any()
    manifest.to_csv(out / 'subject_modality_manifest.csv', index=False)
    pd.DataFrame(conflicts, columns=['site', 'subject_id', 'attribute', 'values_json']).to_csv(out / 'metadata_conflicts.csv', index=False)
    # Save a labeled sidecar, with the limited evidence level explicit in the manifest.
    keyed_roi = roi[['site', 'subject_id', 'raw_id', 'roi_source_row', 'source_rows', 'source_count', 'binary_label']].reset_index(drop=True)
    pd.concat([keyed_roi, x_roi], axis=1).to_csv(out / 'structural_roi_features_with_provenance.csv', index=False)
    count_flags = ['in_structural_strict_manifest', 'in_fmri_445', 'in_historical_fmri_409',
                   'has_roi_metadata', 'has_keyed_smri_pixels', 'paired_assets_445',
                   'paired_assets_historical409', 'paired_clean_metadata409', 'paired_rest_qc409']
    counts = {c: int(manifest[c].sum()) for c in count_flags}
    site_counts = []
    for c in count_flags:
        selected = manifest[manifest[c]]
        for site, group in selected.groupby('site'):
            site_counts.append({'cohort': c, 'site': site, 'n': len(group),
                                'control': int(group.label.eq(0).sum()), 'adhd': int(group.label.eq(1).sum()),
                                'unresolved_label': int(group.label.isna().sum())})
    pd.DataFrame(site_counts).to_csv(out / 'cohort_site_counts.csv', index=False)
    for c in ['paired_assets_445', 'paired_clean_metadata409', 'paired_rest_qc409']:
        manifest[manifest[c]].to_csv(out / (c + '.csv'), index=False)
    # Historical results are inventories, never new runs or comparable across cohorts by default.
    repo = Path(__file__).resolve().parents[2]
    inventory = []
    for _, r in pd.read_csv(repo / 'results/structural_mri_summary.csv').iterrows():
        inventory.append({'modality': 'structural', 'model': r.model, 'n': r.n,
                          'evaluation': r.evaluation, 'auc': r.auc,
                          'metric': 'test_auc' if r.evaluation == 'single_heldout_split' else 'pooled_oof_auc',
                          'source': str(repo / 'results/structural_mri_summary.csv'),
                          'evidence': 'historical_row_level_summary_affected_by_duplicate_subjects_requires_reaudit'})
    for dirname in ['paired_20260907_111654', 'connectivity_cv_20260907_112842', 'temporal_cv_20260907_114340']:
        path = source / 'runs' / dirname / 'summary.csv'
        for _, r in pd.read_csv(path).iterrows():
            inventory.append({'modality': 'functional_or_covariate_baseline', 'model': r.model, 'n': 409,
                              'evaluation': 'fixed_4fold_mixed_site_inner_validation', 'auc': r.mean_auc,
                              'metric': 'mean_fold_auc', 'source': str(path),
                              'label_audit_status': '13 historical primary-cohort labels conflict with participants.tsv; results provisional pending adjudication',
                              'evidence': r.get('source', 'completed_local_experiment'),
                              'pooled_oof_auc': r.pooled_oof_auc, 'sd_auc': r.sd_auc})
    pd.DataFrame(inventory).to_csv(out / 'experiment_inventory.csv', index=False)
    provenance = [{'name': name, 'path': str(path), 'bytes': path.stat().st_size,
                   'sha256': digest(path)} for name, path in source_files.items()]
    pd.DataFrame(provenance).to_csv(out / 'source_hashes.csv', index=False)
    summary = {
        'output_dir': str(out), 'n_union_existing_manifests': len(manifest), 'counts': counts,
        'structural_source_rows_before_verified_exact_collapse': int(structural.source_count.sum()),
        'roi_source_rows_before_verified_exact_collapse': int(roi.source_count.sum()),
        'pixel_source_rows_before_verified_exact_collapse': len(pixel_ids),
        'duplicate_handling': 'Only identical metadata and identical within-subject feature/pixel duplicates collapsed; every original CSV row index retained. Original files unchanged.',
        'cross_site_duplicate_subject_ids': int(manifest.subject_id.duplicated(keep=False).sum()),
        'metadata_conflicts': {c: int(manifest[c + '_conflict'].sum()) for c in ['label', 'age', 'sex']},
        'strict_manifest_t1_missing': None,
        'raw_t1_availability_check': 'Not completed: mounted Drive raw file stat blocks. Candidate readiness uses verified keyed pixel cache, not raw NIfTI accessibility.',
        'strict_manifest_anatomical_qc_not_pass': int((manifest.in_structural_strict_manifest & ~manifest.anatomical_metadata_qc_pass).sum()),
        'pixel_exact_duplicate_rows': int(repeated_pixels.sum()),
        'pixel_constant_rows': int((~pixel_nonconstant).sum()),
        'structural_without_roi': manifest.loc[manifest.in_structural_strict_manifest & ~manifest.has_roi_metadata, ['site', 'subject_id']].to_dict('records'),
        'fmri_without_strict_structural': manifest.loc[manifest.in_fmri_445 & ~manifest.in_structural_strict_manifest, ['site', 'subject_id', 'qc_anat_raw']].to_dict('records'),
        'not_full_adhd200_inventory': True,
        'roi_semantics': '20 atlas ROI mean subject-zscored T1 intensities; not volume or cortical thickness; CSV is pre-ComBat according to notebook',
        'roi_identity_evidence': 'Co-export code applies identical keep mask to features and metadata; no independent image-to-feature recomputation in this audit.',
        'pixel_semantics': 'Three nearby axial slices as pseudo-RGB, not axial/coronal/sagittal triplanar.',
        'no_training_performed': True,
        'no_clinical_or_external_validation_claim': True,
        'limitations': ['Raw T1 presence/size not determined; no new NIfTI readability or registration QC. Pixel cache inspected instead.',
                       'Rest QC is acquisition metadata, not a substitute for motion/QC sensitivity analysis.',
                       'Candidate lists are not a new untouched holdout; these data have been used repeatedly.',
                       'Check NeuroIMAGE data-use permission before new training or redistribution; source participants file includes a permission disclaimer.',
                       'Pittsburgh retained in 445 inventory; changing historical cohort requires a separate declared analysis.'],
    }
    summary = json.loads(json.dumps(summary), parse_constant=lambda _: None)
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    main()
