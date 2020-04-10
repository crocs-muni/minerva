#!/bin/bash

scp -r poc submit join.py task.fish task.sh j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/random_subsets
scp j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/random_subsets/results/runs.pickle results/runs.pickle