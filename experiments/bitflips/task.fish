#!/usr/bin/env fish

# args: datatype curve hash input_file bounds method recenter e n d

if [ (count $argv) -ne 10 ]
    echo "Usage: datatype curve hash input bounds method recenter e n d" >&2
    echo "Error!" >&2
    exit 1
end

set data "$argv[1]"
set curve "$argv[2]"
set hash "$argv[3]"
set input "$argv[4]"
set bounds "$argv[5]"
set method "$argv[6]"
set recenter "$argv[7]"
set e "$argv[8]"
set n "$argv[9]"
set d "$argv[10]"

echo $PBS_JOBID
cat $PBS_NODEFILE

trap "clean_scratch 2>&1 >/dev/null" TERM

function run_atk
    #args: curve1  hash2  input3  params4  fname5
    set fname "$argv[5]"
    set params_temp $SCRATCHDIR/params.json
    set input_temp $SCRATCHDIR/input.csv
    echo "$argv[4]" >$params_temp
    cat "$argv[3]" >$input_temp
    set input_hash (sha256sum $input_temp | cut -d" " -f1)
    set expected_hash (cat "$argv[3].sha256")
    if [ "$input_hash" != "$expected_hash" ]
        echo "Hash mismatch! $input_hash $expected_hash" >&2
        echo "Error!" >&2
        clean_scratch 2>&1 >/dev/null
        exit 1
    end
    if [ ! \( -e "$fname" \) ]
        set runs 5
    else
        set did (wc -l "$fname" | cut -d" " -f1)
        set runs (math "5 - $did")
    end
    for i in (seq $runs)
        set start (date +%s)
        set out ($EXPERIMENT_DIR/poc/attack/attack.py $argv[1] $argv[2] $input_temp -p $params_temp)
        set stop (date +%s)
        set duration (math $stop - $start)
        if echo $out | grep -q "PRIVATE"
            set found 1
            set result_row (echo $out | grep -o "Result row: [0-9]*" | grep -o "[0-9]*")
            set result_normdist (echo $out | grep -o "Result normdist: [0-9\\.e+]*" | cut -d" " -f 3)
            set required_flips (echo $out | grep -o "Required flips: [0-9;]*" | cut -d":" -f 2 | grep -o "[0-9;]*")
            set flip_index (echo $out | grep -o "Flip index: [0-9]*" | grep -o "[0-9]*")        
        else
            set found 0
            set result_row 0
            set result_normdist 0
            set required_flips ""
            set flip_index ""
        end
        set overhead (echo $out | grep -o "overhead [0-9]\\.[0-9]*" | grep -o "[0-9]\\.[0-9]*")
        set info (echo $out | grep -o "[0-9]* bits of information" | grep -o "[0-9]*")
        set random_seed (echo $out | grep -o "Random seed: [0-9]*" | grep -o "[0-9]*")
        set liars (echo $out | grep -o "Liars: [0-9]*" | grep -o "[0-9]*")
        set real_info (echo $out | grep -o "Real info: [0-9]*" | grep -o "[0-9]*")
        set good_info (echo $out | grep -o "Good info: [0-9]*" | grep -o "[0-9]*")
        set bad_info (echo $out | grep -o "Bad info: [0-9]*" | grep -o "[0-9]*")
        set block_size (echo $out | grep -o -E "BKZ-[0-9]*" | tail -n1)
        set liar_positions (echo $out | grep -o "Liar positions: [0-9@;]*" | cut -d":" -f 2 | grep -o "[0-9@;]*")
        if [ -z "$block_size" ]
            set block_size (echo $out | grep -o "SIEVE")
        end
        if [ -z "$block_size" ]
            set block_size (echo $out | grep -o "LLL")
        end
        set num_guesses (echo $out | grep -c "Guess")
        echo "$random_seed,$found,$duration,$block_size,$info,$liars,$real_info,$bad_info,$good_info,$liar_positions,$result_normdist,$result_row,$required_flips,$flip_index" >>"$fname"
    end
    clean_scratch 2>&1 >/dev/null
end

function get_fname
    echo "$EXPERIMENT_DIR/run/$argv[1]_$argv[2]_$argv[3]_$argv[4]_$argv[5]_$argv[6]_$argv[7].csv"
end

set params (cat $EXPERIMENT_DIR/poc/attack/params.json | jq ".attack.num = $n | .dimension = $d | .attack.method = \"$method\" | .recenter = \"$recenter\" | .bitflips = $e")

if string match -q -r -e "^const[0-9]+\$" "$bounds"
    # run const with the diff ls
    set bound (string match -r "[0-9]+" "$bounds" | tail -n1)
    set params (echo $params | jq ".bounds = {\"type\": \"constant\", \"value\": $bound}")
    set fname (get_fname $data "const$bound" $method $recenter $e $n $d)
    echo "Running $bounds $method $recenter"
    run_atk "$curve" "$hash" "$input" "$params" "$fname"
else if string match -q -r -e "^geom[0-9]+\$" "$bounds"
    # run geom with the diff ls
    set bound (string match -r "[0-9]+" "$bounds" | tail -n1)
    set p1 "$bound"
    set p2 (math "$bound" + 1)
    set p4 (math "$bound" + 2)
    set p8 (math "$bound" + 3)
    set p16 (math "$bound" + 4)
    set p32 (math "$bound" + 5)
    set p64 (math "$bound" + 6)
    set p128 (math "$bound" + 7)
    set params (echo $params | jq ".bounds = {\"type\": \"geom\"}")
    set params (echo $params | jq ".bounds.parts = {\"128\": $p128, \"64\": $p64, \"32\": $p32, \"16\": $p16, \"8\": $p8, \"4\": $p4, \"2\": $p2, \"1\": $p1}")
    set fname (get_fname $data "geom$bound" $method $recenter $e $n $d)
    echo "Running $bounds" "$method $recenter"
    run_atk "$curve" "$hash" "$input" "$params" "$fname"
else if string match -q -r -e "^geomN(i[0-9]+)?(m[0-9]+)?(x[0-9]+)?\$" "$bounds"
    set params (echo $params | jq ".bounds = {\"type\": \"geomN\"}")
    set iparam (echo "$bounds" | grep -E -o "i[0-9]+" | grep -E -o "[0-9]+")
    if [ -n "$iparam" ]
        set params (echo $params | jq ".bounds.index = $iparam")
    end
    set mparam (echo "$bounds" | grep -E -o "m[0-9]+" | grep -E -o "[0-9]+")
    if [ -n "$mparam" ]
        set params (echo $params | jq ".bounds.value = $mparam")
    end
    set xparam (echo "$bounds" | grep -E -o "x[0-9]+" | grep -E -o "[0-9]+")
    if [ -n "$xparam" ]
        set xvalue (math "$xparam" / 100)
        set params (echo $params | jq ".bounds.multiple = $xvalue")
    end
    set fname (get_fname $data "geomN" $method $recenter $e $n $d)
    echo "Running $bounds $method $recenter"
    run_atk "$curve" "$hash" "$input" "$params" "$fname"
else if string match -q -r -e "^known\$" "$bounds"
    set params (echo $params | jq ".bounds = {\"type\": \"known\"}")
    set fname (get_fname $data "known" $method $recenter $e $n $d)
    echo "Running known $method $recenter"
    run_atk "$curve" "$hash" "$input" "$params" "$fname"
else if string match -q -r -e "^template[0-9]+\$" "$bounds"
    # alpha is a percent
    set alpha (string match -r "[0-9]+" "$bounds" | tail -n1)
    set temp_bounds (cat $data.json | jq ".\"$alpha\".\"$d\".\"$n\"")
    set params (echo $params | jq ".bounds = $temp_bounds")
    set params (echo $params | jq ".bounds.type = \"template\"")
    set l (math "$alpha * 100" | cut -d"." -f 1)
    set l (printf "%02i" "$l")
    set fname (get_fname $data "template$l" $method $recenter $e $n $d)
    echo "Running template$l $method $recenter"
    run_atk "$curve" "$hash" "$input" "$params" "$fname"
end

echo $fname
echo $params | jq