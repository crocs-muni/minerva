#!/usr/bin/env fish

set EXPERIMENT_DIR "$ARTIFACT_DIR/experiments/bounds"
set task "$EXPERIMENT_DIR/task.sh"

export ARTIFACT_DIR
export EXPERIMENT_DIR
while read todo
    set todo_parts (string split "_" "$todo")
    set data $todo_parts[1]
    set bounds $todo_parts[2]
    set n $todo_parts[3]
    set d $todo_parts[4]

    if [ "$data" = "card" ]
        set hash "sha256"
        set fname "data_athena.csv"
    else if [ "$data" = "sw" ]
        set hash "sha1"
        set fname "data_gcrypt.csv"
    else if [ "$data" = "sim" ]
        set hash "sha1"
        set fname "data_sim.csv"
    else if [ "$data" = "tpm" ]
        set hash "sha256"
        set fname "data_tpmfail_stm.csv"
    end
    set walltime "00:$d:00"
    echo $data $n $d
    set task_name minerva_""$data""_""$bounds""_""$n""_$d
    qsub -v ARTIFACT_DIR,EXPERIMENT_DIR -W umask=002 -W group_list=crocs -q @meta-pbs.metacentrum.cz -N $task_name -e $EXPERIMENT_DIR/logs/$task_name.err -o $EXPERIMENT_DIR/logs/$task_name.out -l select=1:ncpus=1:mem=1gb -l walltime=$walltime -- $task $data secp256r1 $hash $ARTIFACT_DIR/data/$fname $bounds $n $d
end