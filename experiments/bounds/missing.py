#!/usr/bin/env python
import argparse
import itertools as it
from join import load_transformed, AttackRun

d_list = list(range(50, 142, 2))
n_list = list(it.chain(range(500, 7100, 100), range(8000, 11000, 1000)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--bounds", type=str, required=True)
    args = parser.parse_args()

    data_types = args.data.split(",")
    bound_types = args.bounds.split(",")
    runs = load_transformed("runs.pickle")
    present = set()
    for run in runs:
        if run.dataset in data_types and run.bounds in bound_types:
            present.add((run.N, run.d, run.dataset, run.bounds))
    for n in n_list:
        for d in d_list:
            for dataset in data_types:
                for bounds in bound_types:
                    if (n, d, dataset, bounds) not in present:
                        print(dataset, bounds, n, d, sep="_")