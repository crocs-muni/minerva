#!/bin/bash
# This script is the one that is submitted for the job.
# It prepares the environment for the fish script

source /software/modules/init
module add python/3.8.0
cd $ARTIFACT_DIR
. activate.sh
cd $EXPERIMENT_DIR
fish task.fish "$@"