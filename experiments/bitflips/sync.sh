#!/bin/bash

scp -r poc submit join.py missing.py present.py task.fish task.sh j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/bitflips
scp j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/bitflips/results/runs.pickle results/runs.pickle