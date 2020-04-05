#!/bin/bash

scp -r poc submit info.md info.pdf join.py missing.py plot.py plot_new.py present.py task.fish task.sh j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/bounds
scp j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/bounds/results/runs.pickle results/runs.pickle