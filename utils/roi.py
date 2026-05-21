"""
utils/roi.py
Harvard-Oxford atlas ROI mask construction for ADHD-relevant circuits.
"""

import numpy as np
import nibabel as nib
from nilearn import datasets


# Default ADHD-relevant cortical ROI names (PFC + cingulate)
CORT_ROI_NAMES = [
    "Frontal Pole",
    "Superior Frontal Gyrus",
    "Middle Frontal Gyrus",
    "Inferior Frontal Gyrus, pars triangularis",
    "Inferior Frontal Gyrus, pars opercularis",
    "Frontal Medial Cortex",
    "Frontal Orbital Cortex",
    "Paracingulate Gyrus",
    "Cingulate Gyrus, anterior division",
    "Cingulate Gyrus, posterior division",
]

# Default subcortical ROI names (striatum + thalamus)
SUB_ROI_NAMES = [
    "Thalamus",
    "Caudate",
    "Putamen",
    "Pallidum",
    "Accumbens",
]


def _idx_by_name(labels, name_fragment: str):
    key = name_fragment.lower()
    return [
        i for i, lab in enumerate(labels)
        if key in str(lab if not isinstance(lab, bytes) else lab.decode("utf-8", errors="ignore")).lower()
    ]


def build_roi_mask(
    cort_roi_names=None,
    sub_roi_names=None,
    min_voxels_per_slice: int = 200,
    max_slices: int = 16,
    evenly_spaced: bool = True,
    seed: int = 42,
):
    """
    Build a binary ROI mask in MNI152 2mm space using the Harvard-Oxford atlas,
    and select z-slices with sufficient ROI coverage.

    Args:
        cort_roi_names: list of cortical region name fragments to include.
        sub_roi_names: list of subcortical region name fragments to include.
        min_voxels_per_slice: minimum ROI voxels for a z-slice to be selected.
        max_slices: maximum number of z-slices to use per subject.
        evenly_spaced: if True, pick evenly-spaced slices; else random sample.
        seed: random seed for slice sampling.

    Returns:
        roi_mask (np.ndarray bool, shape MNI 2mm),
        roi_z (list of int, selected z-slice indices)
    """
    if cort_roi_names is None:
        cort_roi_names = CORT_ROI_NAMES
    if sub_roi_names is None:
        sub_roi_names = SUB_ROI_NAMES

    ho_cort = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr25-2mm")
    ho_sub = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr25-2mm")

    def _as_nii(obj):
        return obj if isinstance(obj, nib.spatialimages.SpatialImage) else nib.load(obj)

    cort_img = _as_nii(ho_cort.maps)
    sub_img = _as_nii(ho_sub.maps)

    cort_data = cort_img.get_fdata().astype(int)
    sub_data = sub_img.get_fdata().astype(int)
    cort_labels = list(ho_cort.labels)
    sub_labels = list(ho_sub.labels)

    cort_ids = sorted(set(
        idx for nm in cort_roi_names for idx in _idx_by_name(cort_labels, nm) if idx != 0
    ))
    sub_ids = sorted(set(
        idx for nm in sub_roi_names for idx in _idx_by_name(sub_labels, nm) if idx != 0
    ))

    roi_mask = np.zeros_like(cort_data, dtype=bool)
    for rid in cort_ids:
        roi_mask |= (cort_data == rid)
    for rid in sub_ids:
        roi_mask |= (sub_data == rid)

    counts = roi_mask.sum(axis=(0, 1))
    eligible_z = np.where(counts >= min_voxels_per_slice)[0].tolist()
    assert eligible_z, "No eligible ROI z-slices. Lower min_voxels_per_slice."

    if len(eligible_z) <= max_slices:
        roi_z = eligible_z
    elif evenly_spaced:
        idx = np.linspace(0, len(eligible_z) - 1, max_slices).round().astype(int)
        roi_z = sorted(list(dict.fromkeys(eligible_z[i] for i in idx)))
    else:
        rng = np.random.default_rng(seed)
        roi_z = sorted(rng.choice(eligible_z, size=max_slices, replace=False).tolist())

    return roi_mask, roi_z
