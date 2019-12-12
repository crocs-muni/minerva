#!/usr/bin/env fish

# args: datatype curve hash input_file bounds n d

if [ (count $argv) -ne 7 ]
    echo "Usage: datatype curve hash input bounds n d"
    echo "Error!"
    exit 1
end

set data "$argv[1]"
set curve "$argv[2]"
set hash "$argv[3]"
set input "$argv[4]"
set bounds "$argv[5]"
set n "$argv[6]"
set d "$argv[7]"

function run_atk
    #args: curve1  hash2  input3  params4 
    set temp (mktemp)
    echo "$argv[4]" > $temp
    for i in (seq 5)
        set start (date +%s)
        set out (./poc/attack/attack.py $argv[1] $argv[2] $argv[3] -p $temp)
        set stop (date +%s)
        set duration (math $stop - $start)
        if echo $out | grep -q "PRIVATE"
            set found 1
            set result_row (echo $out | grep -o "Result row: [0-9]*" | grep -o "[0-9]*")
            set result_normdist (echo $out | grep -o "Result normdist: [0-9\\.]*" | cut -d" " -f 3)
        else
            set found 0
            set result_row 0
            set result_normdist 0
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
            set block_size "LLL"
        end
        set num_guesses (echo $out | grep -c "Guess")
        echo "$random_seed,$found,$duration,$block_size,$info,$liars,$real_info,$bad_info,$good_info,$liar_positions,$result_normdist,$result_row"
    end
    rm -f $temp
end

function get_fname
    echo "/storage/brno2/home/j08ny/minerva/experiments/bounds/run/$argv[1]_$argv[2]_$argv[3]_$argv[4].csv"
end

set params (cat ./poc/attack/params.json | jq ".attack.num = $n | .dimension = $d")

if string match -r "const\(.*\)" "$bounds"
    # run const with the diff ls
    set l (string match -r "\((.*)\)" "$bounds" | tail -n1)
    for bound in (string split "," $l)
        set params (echo $params | jq ".bounds = {\"type\": \"constant\", \"value\": $bound}")
        set fname (get_fname $data "const$bound" $n $d)
        echo "Running const$bound"
        run_atk "$curve" "$hash" "$input" "$params" > $fname
    end
else if string match -r "geom\(.*\)" "$bounds"
    # run geom with the diff ls
    set l (string match -r "\((.*)\)" "$bounds" | tail -n1)
    for bound in (string split "," $l)
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
        set fname (get_fname $data "geom$bound" $n $d)
        echo "Running geom$bound"
        run_atk "$curve" "$hash" "$input" "$params" > $fname
    end
else if string match -r "geomN" "$bounds"
    set params (echo $params | jq ".bounds = {\"type\": \"geomN\"}")
    set fname (get_fname $data "geomN" $n $d)
    echo "Running geomN"
    run_atk "$curve" "$hash" "$input" "$params" > $fname
else if string match -r "known" "$bounds"
    set params (echo $params | jq ".bounds = {\"type\": \"known\"}")
    set fname (get_fname $data "known" $n $d)
    echo "Running known"
    run_atk "$curve" "$hash" "$input" "$params" > $fname
else if string match -r "known_re" "$bounds"
    set params (echo $params | jq ".bounds = {\"type\": \"known_re\"}")
    set fname (get_fname $data "knownre" $n $d)
    echo "Running knownre"
    run_atk "$curve" "$hash" "$input" "$params" > $fname
else if string match -r "template\(.*\)" "$bounds"
    # alpha is a percent
    set alpha (string match -r "\((.*)\)" "$bounds" | tail -n1)
    set temp_bounds (cat $data.json | jq ".\"$alpha\".\"$d\".\"$n\"")
    set params (echo $params | jq ".bounds = $temp_bounds")
    set params (echo $params | jq ".bounds.type = \"template\"")
    set l (math "$alpha * 100" | cut -d"." -f 1)
    set l (printf "%02i" "$l")
    set fname (get_fname $data "template$l" $n $d)
    echo "Running template$l"
    run_atk "$curve" "$hash" "$input" "$params" > $fname
end
echo $argv
echo "done"