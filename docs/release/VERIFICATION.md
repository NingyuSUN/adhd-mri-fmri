# Release verification — 2026-09-10

- **Installed package:** final wheel built and installed locally with no dependency downloads; imported all 12 preserved scientific modules.
- **Tests:** 19 tests passed, zero failures/errors/skips, executed against the installed final wheel with the existing recorded Windows CPU dependencies.
- **Synthetic example:** original LR/MLP workflow ran on 120 synthetic examples and passed saved-checkpoint replay. Timing is scoped to the toy run.
- **Real evidence:** independently replayed 35,910 test predictions and 60 validation-selected fusion weights. Maximum summary disagreement was about 1.1e-16. All source files used by the replay matched the frozen manifest.
- **Real preparation:** generated the original 378-person, five-repeat / three-fold split metadata and training covariate setup without model training. All three full-stage preflights found their required inputs and matched the recorded numerical environment.
- **Source preservation:** 11 archived modules preserve original bytes; run_paired.py is separately labeled as a transitive runtime supplement. Git attributes preserve source bytes across operating systems.
- **Presentation:** all 10 editable slides rendered and visually inspected; Chinese notes on all pages; single-page PDF rendered and checked. A minor chart-label spacing issue was corrected.
- **Independent review:** one important finding about unignored individual validation records was addressed with both file patterns. No other important numerical or path issues were reported.
- **Commit scope:** aggregate tables and source/documentation only; no participant-level records, raw scans, feature arrays or model checkpoints were staged. Original structural CRLF-only working changes were preserved outside this commit.

Limits: this release did not repeat the full real-data training or reconstruct raw-image preprocessing. Wheel installation reused existing dependencies; a fresh dependency environment on another OS has not been tested. GitHub-hosted CI is configured, not yet executed here. Repeated internal results are not an external validation, confidence interval, equivalence or calibrated clinical-risk claim.

Machine-readable records: [model evidence](../../results/fmri_378/verification.json), [package verification](../../results/fmri_378/package_verification.json), [synthetic run](../../results/fmri_378/synthetic_demo.json).
