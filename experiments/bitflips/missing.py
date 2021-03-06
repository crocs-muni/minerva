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
    parser.add_argument("--methods", type=str, required=True)
    parser.add_argument("--recenter", type=str, required=True)
    parser.add_argument("--e", type=str, required=True)
    parser.add_argument("-m", "--min", type=int, default=1, dest="m")
    args = parser.parse_args()

    data_types = args.data.split(",")
    bound_types = args.bounds.split(",")
    method_types = args.methods.split(",")
    recenter_types = args.recenter.split(",")
    e_types = args.e.split(",")
    runs = load_transformed("results/runs.pickle")
    present = {}
    for run in runs:
        if run.dataset in data_types and run.bounds in bound_types and run.method in method_types and run.recenter in recenter_types and run.e in e_types:
            present.setdefault((run.N, run.d, run.dataset, run.bounds, run.method, run.recenter, run.e), 0)
            present[(run.N, run.d, run.dataset, run.bounds, run.method, run.recenter, run.e)] += 1
    for n in n_list:
        for d in d_list:
            for dataset in data_types:
                for bounds in bound_types:
                    for method in method_types:
                        for recenter in recenter_types:
                            for e in e_types:
                                key = (n, d, dataset, bounds, method, recenter, e)
                                if key not in present or present[key] < args.m:
                                    print(dataset, bounds, method, recenter, e, n, d, sep="_")
