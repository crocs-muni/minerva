#!/usr/bin/env python
import itertools as it
from join import load_transformed, AttackRun

d_list = list(range(50, 142, 2))
n_list = list(it.chain(range(500, 7100, 100), range(8000, 11000, 1000)))

if __name__ == "__main__":
    data_types = ("sw", "card", "sim")
    bound_types = ("known", "knownre", "geom", "geom1", "geom2", "geom3", "geom4", "geomN", "const1", "const2", "const3", "const4", "template01", "template10", "template30", "templatem01", "templatem10", "templatem30")
    runs = load_transformed("results/runs.pickle")
    present = {}
    for run in runs:
        val = present.setdefault((run.N, run.d, run.dataset, run.bounds), 0)
        present[(run.N, run.d, run.dataset, run.bounds)] += 1
    for dataset in data_types:
        for bounds in bound_types:
            count = 0
            all_there = True
            for n in n_list:
                for d in d_list:
                    if (n, d, dataset, bounds) not in present:
                        all_there = False
                    else:
                        count += present[(n, d, dataset, bounds)]
            print(dataset, bounds, count, all_there)



