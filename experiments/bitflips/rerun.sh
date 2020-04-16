#!/bin/bash

missing=$(./missing.py $@)
for miss in $missing; do
	name=minerva_${miss}
	if [ -z "$(qselect -N $name -q @meta-pbs.metacentrum.cz -s QR)" ] && [ -z "$(qselect -N $name -q @elixir-pbs.elixir-czech.cz -s QR)" ] && [ -z "$(qselect -N $name -q @cerit-pbs.cerit-sc.cz -s QR)" ]; then
		echo $miss		
	fi
done
