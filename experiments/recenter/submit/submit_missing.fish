#!/usr/bin/env fish

set EXPERIMENT_DIR "$ARTIFACT_DIR/experiments/recenter"
set task "$EXPERIMENT_DIR/task.sh"

if [ (count $argv) -eq 1 ]
  if [ "$argv[1]" = "meta" ]
    set pbs_server "@meta-pbs.metacentrum.cz"
  else if [ "$argv[1]" = "cerit" ]
    set pbs_server "@cerit-pbs.cerit-sc.cz"
  else if [ "$argv[1]" = "elixir" ]
    set pbs_server "@elixir-pbs.elixir-czech.cz"
  else
    echo "Bad PBS server!" >&2
    exit 1
  end
else
  set pbs_server "@meta-pbs.metacentrum.cz"
end

export ARTIFACT_DIR
export EXPERIMENT_DIR
while read todo
    set todo_parts (string split "_" "$todo")
    if [ (count "$todo_parts") -ne 6 ]
        echo "Bad input: $todo_parts" >&2
        continue
    end
    set data $todo_parts[1]
    set bounds $todo_parts[2]
    set method $todo_parts[3]
    set recenter $todo_parts[4]
    set n $todo_parts[5]
    set d $todo_parts[6]

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
    echo $data $bounds $method $recenter $n $d
    set task_name minerva_""$data""_""$bounds""_""$method""_""$recenter""_""$n""_$d
    qsub -v ARTIFACT_DIR,EXPERIMENT_DIR -W umask=002 -W group_list=crocs -q $pbs_server -N $task_name -e $EXPERIMENT_DIR/logs/$task_name.err -o $EXPERIMENT_DIR/logs/$task_name.out -l select=1:ncpus=1:mem=1gb:cl_adan=False -l walltime=$walltime -- $task $data secp256r1 $hash $ARTIFACT_DIR/data/$fname $bounds $method $recenter $n $d
end