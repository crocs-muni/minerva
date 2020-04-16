#!/usr/bin/env python

from join import load_transformed, AttackRun

if __name__ == "__main__":
    runs = load_transformed("results/runs.pickle")
    runtime = 0
    for run in runs:
        runtime += run.time
    print(runtime)