This directory contains the R scripts to plot Figure 1-5 contained in the paper.

Note that the scripts are intended to be invoked by the Makefile in the `$ARTIFACT_ROOT/paper` directory. The Makefile also manages the dependencies of the plot scripts (i.e., the .csv files needed to build them).

To test whether this part of the artifact works correctly, you can delete the plots and build them again:

```
rm -r $ARTIFACT_ROOT/generated/plots/*
cd $ARTIFACT_ROOT/paper
make plots
```
