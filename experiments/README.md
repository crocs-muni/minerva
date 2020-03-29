# Experiments

**[METACENTRUM ONLY]**

## Experiment workflow

Before running any experiments, make sure you sourced the `activate.sh` script at the
root of the artifact.

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