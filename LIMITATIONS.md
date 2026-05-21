# Limitations

## 1. ADHD signal in T1 MRI is weak

ADHD is likely more strongly reflected in functional/network-level abnormalities than in gross anatomical T1 structure. Structural signals may be subtle, distributed, site-dependent, and difficult to capture with small-sample CNNs.

## 2. Multi-site site bias is a major threat

ADHD-200 combines data from multiple acquisition sites. Site can correlate with diagnosis rate, scanner parameters, image intensity distribution, age, and sex composition. Therefore, apparent model performance may reflect site recognition rather than ADHD biology.

## 3. Slice-based 2D CNNs are simplified approximations

2D slice models reduce computational burden and improve interpretability, but they discard 3D spatial context. They should be interpreted as baselines rather than final performance ceilings.

## 4. ROI priors may be incomplete

The selected fronto-striatal/cingulate regions are motivated by ADHD neurobiology, but ADHD-related differences may also involve distributed networks not captured by these ROI slices.

## 5. fMRI preprocessing is simplified in the current prototype

The current fMRI scripts focus on graph construction and model feasibility. Publication-level fMRI analysis should carefully document motion correction, nuisance regression, temporal filtering, scrubbing, and site harmonization.

## 6. GNN sample size and graph definition remain bottlenecks

Early fMRI GNN runs are sensitive to ROI extraction, graph construction, and sample retention. Fixed ROI representation must be enforced before model performance is interpreted.

## 7. Not clinically deployable

This project is a research investigation. It is not validated for clinical diagnosis, screening, or treatment decision-making.
