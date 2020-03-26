#!/bin/bash

export ARTIFACT_DIR="/storage/brno3-cerit/home/j08ny/minerva"
export PATH="$PATH:$ARTIFACT_DIR/.local/bin"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$ARTIFACT_DIR/.local/lib"
export PKG_CONFIG_PATH="$PKG_CONFIG_PATH:$ARTIFACT_DIR/.local/lib/pkgconfig"
. virt/bin/activate
