#!/usr/bin/env fish

if [ (count $argv) -ne 5 ]
    echo "Must specify data, bounds, methods, recenter type and c constant." >&2
    exit 1
end
set data $argv[1]
set bounds $argv[2]
set method $argv[3]
set recenter $argv[4]
set c $argv[5]

set EXPERIMENT_DIR "$ARTIFACT_DIR/experiments/random_subsets"
set task "$EXPERIMENT_DIR/task.sh"

export ARTIFACT_DIR
export EXPERIMENT_DIR
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
for d in (seq 90 2 100)
    #set seconds_per_atk (math "(400/90) * ($d - 50) + 200")
    set seconds_per_atk 250
    set atks 500
    set total_secs (math "$seconds_per_atk * $atks")
    set minutes (math "$total_secs / 60" | cut -d"." -f1)
    set walltime "00:$minutes:00"
    for n in (seq 500 100 7000) (seq 8000 1000 10000)
        echo $data $bounds $method $recenter $c $n $d
        set task_name minerva_""$data""_""$bounds""_""$method""_""$recenter""_""$c""_""$n""_$d
        qsub -v ARTIFACT_DIR,EXPERIMENT_DIR -W umask=002 -W group_list=crocs -P minerva_random_subsets_exp -N $task_name -q @meta-pbs.metacentrum.cz -e $EXPERIMENT_DIR/logs/$task_name.err -o $EXPERIMENT_DIR/logs/$task_name.out -l select=1:ncpus=1:mem=512mb:scratch_local=512mb -l walltime=$walltime -- $task $data secp256r1 $hash $ARTIFACT_DIR/data/$fname $bounds $method $recenter $c $n $d
    end
end