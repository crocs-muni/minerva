#!/bin/bash

meta=$(qselect -P minerva_bitflips_exp -s QR -q @meta-pbs.metacentrum.cz)
elixir=$(qselect -P minerva_bitflips_exp -s QR -q @elixir-pbs.elixir-czech.cz)
cerit=$(qselect -P minerva_bitflips_exp -s QR -q @cerit-pbs.cerit-sc.cz)

for job_id in $meta $elixir $cerit; do
	job=$(qstat -f -F dsv $job_id | grep -P -o "Job_Name=.*?\|")
	job_name=${job:9:-1}
	echo $job_name
done