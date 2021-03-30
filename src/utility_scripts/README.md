# /src/utility_scripts

This folder contains code for the performance analysis of aubioonset.

- `customAubio/` contains a custom executable for aubioonset that simply disables Adaptive Whitening in initialization.
- `r_analysis/` contains a R project that extracts relevant metrics from labeled and extracted onsets
- `extractAllOnsets.sh` calls extractOnset for each recording in a folder.
- `extractOnset.sh` calls the specified aubioonset executable for a specific recording, with the specified parameters. It saves the extracted onset times in a text file.
- `fixLabels.sh` is a simple script that converts a onset times txt file in a label file which is compatible with audacity (for visualization and more).
