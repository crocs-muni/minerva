#!/bin/bash

scp -r poc submit task.fish task.sh j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/recenter
scp j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/recenter/results/runs.pickle results/runs.pickle