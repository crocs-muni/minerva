#!/usr/bin/env python
from join import load_transformed, AttackRun

if __name__ == "__main__":
    runs = load_transformed("results/runs.pickle")
    present = {}
    for run in runs:
        val = present.setdefault((run.dataset, run.bounds, run.method), 0)
        present[(run.dataset, run.bounds, run.method)] += 1
    for k, v in sorted(present.items()):
        print("_".join(k), v)
