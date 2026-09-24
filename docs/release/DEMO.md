# Three-minute technical demo

Audience: medical AI or general DS/MLE. Use English on screen; Chinese presenter notes are also in the technical deck. The small executable demonstration is synthetic; use the separate verified tables to discuss actual ADHD findings.

## 0:00–0:40 — Problem and evidence

Open the README. Explain two questions: improving image representation and measuring its gain over the full non-imaging control. Point to 0.6096 → 0.6453, then 0.7077 → 0.7127. Say explicitly that these are repeated internal estimates.

## 0:40–1:20 — Show a real pipeline running

```bash
python -m adhd_fmri_benchmark demo --out artifacts/demo-001
```

The terminal identifies synthetic data. Open `demo.json` and the generated training history: show validation-selected C, early stopping, checkpoint replay and measured time. These timings apply only to this toy workload; neither score is a new ADHD result.

## 1:20–2:10 — Show the tests and real evidence

```bash
python -m unittest discover -s tests -v
```

Explain one perturbation test: changing held-out values/labels leaves training feature selection/scaling unchanged. Open `results/fmri_378/verification.json`: 35,910 frozen test rows, 60 selected fusion weights, matching AUCs. The public file is the audit record; actual replay requires the separately held frozen prediction archive.

## 2:10–3:00 — Explain one engineering decision

Show `sources.json` and the reproduction guide. I preserved scientific source hashes, added path relocation around them, and separated synthetic execution, prediction replay and complete scientific refitting. I corrected a float32/float64 replay discrepancy by matching the original operation order rather than loosening the tolerance. Finish with the appropriate emphasis:

- Medical AI: data/QC and confound baselines govern what can be inferred; current fMRI does not establish across-hospital utility.
- DS/MLE: data contracts, repeatable execution, checkpoints, numerical debugging and clear validation gates make the model result reviewable.

## Example observed local run

The committed [synthetic run record](../../results/fmri_378/synthetic_demo.json) records 120 generated examples, a 60/30/30 split and passed checkpoint replay. The original 1,000-input MLP has 65,121 parameters; this 12-feature synthetic example has 1,889. Timing varies by machine and dependency version.
