#!/bin/bash

#rsync -v -r $ARTIFACT_DIR/experiments --exclude="experiments/*/run" --exclude="experiments/*/results" --exclude="experiments/*/logs" --exclude="__pycache__" j08ny@skirit.metacentrum.cz:/storage/brno3-cerit/home/j08ny/minerva
scp -r poc submit .gitignore info.md info.pdf join.py missing.py plot.py plot_new.py present.py task.fish task.sh j08ny@skirit.metacentrum.cz:/storage/brno3-cerit/home/j08ny/minerva/experiments/bounds
scp j08ny@skirit.metacentrum.cz:/storage/brno3-cerit/home/j08ny/minerva/experiments/bounds/results/runs.pickle results/runs.pickle