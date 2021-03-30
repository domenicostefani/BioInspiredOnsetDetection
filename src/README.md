# /src

This folder contains code and data for the performance analysis of aubioonset.

- `audiofiles/` contains a small dataset of individual sounds from acoustic guitars, used for evaluation.
- `onsets_labeled/` contains millisecond-accurate onset labels (manually annotated) for the aforementioned recordings. These are in audacity format to facilitate visualization.
- `utility_scripts/` contains code that helps to extract onsets from the recordings (bash) and analyze results (R).
- `VERSION` contains the version of aubio in analysis, correct functioning is not guaranteed with other versions.
- `computeLatency.py` is a script that ties in all the functionalities for manual analysis of aubioonset. It calls various scripts in `utility_scripts/` and it relies on the current directory organization.
- `evolutionaryoptimizer.py` contains a bio-inspired automatic optimizer for aubio. It imports `computeLatency.py` as a module and uses it for evaluation of its solutions.
- `run_all_eas.sh` is a simple script that calls one instance of the optimizer for each OD methods, at one specific buffer size (argument). It logs completion times.
