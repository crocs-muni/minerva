#!/usr/bin/env fish

set EXPERIMENT_DIR "$ARTIFACT_DIR/experiments/bounds"
set task "$EXPERIMENT_DIR/task.sh"

export $ARTIFACT_DIR
epxort $EXPERIMENT_DIR
for data in "sim" "sw" "card"
    if [ "$data" = "card" ]
        set hash "sha256"
        set fname "data_athena.csv"
    else if [ "$data" = "sw" ]
        set hash "sha1"
        set fname "data_gcrypt.csv"
    else if [ "$data" = "sim" ]
        set hash "sha1"
        set fname "data_sim.csv"
    end
    for d in (seq 50 2 140)
        set walltime "00:$d:00"
        for n in (seq 500 100 7000) (seq 8000 1000 10000)
            echo $data $n $d
            qsub -v ARTIFACT_DIR,EXPERIMENT_DIR -N minerva_card_geomN_""$n""_$d -l select=1:ncpus=1:mem=1gb -l walltime=$walltime -- $task $data secp256r1 $hash $ARTIFACT_DIR/data/$fname "geomN" $n $d
        end
    end
end
