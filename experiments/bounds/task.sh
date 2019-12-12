#!/bin/bash

source /software/modules/init
module add python36-modules-gcc
export PATH="$PATH:/storage/brno2/home/j08ny/.local/bin/:/storage/brno2/home/j08ny/bin/"
cd "/storage/brno2/home/j08ny/minerva/"
. virt/bin/activate
cd "experiments/bounds"
fish task.fish "$@"