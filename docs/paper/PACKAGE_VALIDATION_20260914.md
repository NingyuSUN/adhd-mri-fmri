# Package validation — 2026-09-14

VERIFIED: 34 selected aggregate server files match SHA-256. Server synthetic suite: 18 passed in 3.68s. The integrity/statistics tests and completion/integrity/statistical modules match local hashes. The local completion test file differs: it includes a later finisher guard test; the server 18-test result must not be represented as a pass of the local full suite. Local full-suite execution remains NOT VERIFIED. This checks engineering invariants, not statistical assumptions or external performance.

Exact test command on SV002:
```
<AUDIT_PYTHON> -m pytest <AUDIT_ROOT>/reviewed_tools/reproduction/tests -q
```
No training/full verifier was rerun. Initial local pytest was unavailable; an initial server test path omitted the reproduction subdirectory and ran no tests. The corrected command above passed.

Fable source review: COMPLETE after explicit payload authorization; see FABLE_REVIEW_TRIAGE_20260914.md for adjudication and limitations. Human expert review: NOT VERIFIED.

## Local source snapshot follow-up

VERIFIED after explicit review authorization: all 19 current local synthetic tests passed in 3.95s using the existing server audit environment in a temporary directory, subsequently removed. Source hashes and raw test output are recorded in `results/paper_readiness_20260911/local_source_tests_20260914.txt`. This closes the local-suite gap described above; the earlier 18-test statement remains historical. No training or full verification ran.
