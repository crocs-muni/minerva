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

## Bounds