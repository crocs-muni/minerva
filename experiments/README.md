# Experiments

**[METACENTRUM ONLY]**
This directory is only usable to run the experiments on [Metacentrum](https://metacentrum.cz/en/),
the Czech National Grid Infrastructure. It uses the PBS Professional job submission/management system 
so it could be adapted easily to other deployments of it. The experiments could also be adapted 
to run locally, although the are computationaly heavy.

## Experiment workflow

Before running any experiments, make sure you sourced the `activate.sh` script at the root of the artifact.

Use fish scripts in `submit` directory to submit jobs. This script sets up `EXPERIMENT_DIR` and passes it to jobs.
It actually submits the `task.sh` script as the job. This script is just a simple BASH wrapper
around `task.fish` that sets some environment variables and sources the `activate.sh` script on
the job worker. It then passes all arguments to the `task.fish` script. This script is somewhat
important, it parses the command line arguments and prepares the inputs to the `attack.py` script.
It sets up the parameters as a JSON file in a temporary directory, it also searches the output of
the `attack.py` and produces CSV output from it in the `run` directory of the experiment.

This produces a lot of files, transferring/compressing them would be lengthy, so they are joined using the `join.py` script
which automatically parses the `run` directory and adds all the runs into the `runs.pickle` file at the root.

The `missing.py` script is useful when some runs of a particular experiment are missing as it produces
a list of them from the `results/runs.pickle` file. This can be passed to the `submit/submit_missing.fish`
script which will submit them as jobs.

The `present.py` is a script for listing the contents of the `results/runs.pickle` file.

Use `plot_new.py` for plotting.  

## Bounds

Experiment to study what bounds to use in the attack.

See [info](bounds/info.md).

## Methods

Experiment to study what lattice techniques to use in the attack (SVP/CVP/...).

See [info](methods/info.md).

## Recenter

Experiment to study the effects of recentering.

See [info](recenter/info.md).

## Differences

Experiment to study the effects of taking the differences of nonces, instead of
the nonces themselves, into the lattice.

See [info](differences/info.md).

## Random subsets

Experiment to study the effect of taking random subsets of signatures (in order
to eliminate errors).

This experiment was run twice, because the first try
was misconfigured. See `random_subsets` directory for the proper one.

See [info](random/info.md) and [info](random_subsets/info.md)

## Bitflips

Experiment to study the approach of error correction using CVP + bitflips.

See [info](bitflips/info.md).