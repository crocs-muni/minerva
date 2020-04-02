#!/bin/bash

scp -r poc submit task.fish task.sh j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/methods
scp j08ny@storage-brno3-cerit.metacentrum.cz:minerva/experiments/methods/results/runs.pickle results/runs.pickle