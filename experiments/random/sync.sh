#!/bin/bash

scp -r poc submit join.py present.py task.fish task.sh j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/random
scp j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/random/results/runs.pickle results/runs.pickle