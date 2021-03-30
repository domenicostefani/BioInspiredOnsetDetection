# /src/utility_scripts/customAubio

This folder contains a modified executable of aubioonset (library version specified in the version file in /src).
What the mod does is simply to disable Adaptive Whitening in the initialization for the mkl method, since it was found to have a detrimental effect in the results.
It's a hacky way of doing things but aubioonset enables AW on initialization for some methods and does not allow to specify this as a parameter.

If you need a version fora different architecture, just rename `ADDTHISTOAUBIOaubioonset.c` to `aubioonset.c`, replace the original file in Aubio source and recompile the examples.
It should work fine as long as you use the same version specified in /src/VERSION

The only edit from the original file at rows `86-87`
