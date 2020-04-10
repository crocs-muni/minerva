#!/usr/bin/env python3
from collections import namedtuple
import pickle
import itertools as it
from os.path import join, exists
from glob import glob
import csv

AttackRun = namedtuple("AttackRun", ("dataset", "bounds", "method", "recenter", "c", "N", "d", "n_seed", "d_seed", "success", "time", "block_size", "info", "liars", "real_info", "bad_info", "good_info", "liar_positions", "normdist", "row"), defaults={"liar_positions": None, "normdist":None, "row": None})

def load_data(data_type, bound_type, method_type, recenter, c, d_range, n_range):
    runs = set()
    fnames = glob(join("run", "{}_{}_{}_{}_{}*.csv".format(data_type, bound_type, method_type, recenter, c)))
    if len(fnames) == 0:
        return runs
    for d in d_range:
        for n in n_range:
            fname = join("run","{}_{}_{}_{}_{}_{}_{}.csv".format(data_type, bound_type, method_type, recenter, c, n, d))
            if fname in fnames:
                with open(fname, newline="") as f:
                    r = csv.reader(f)
                    for line in r:
                        try:
                            n_seed = int(line[0])
                            d_seed = int(line[1])
                            success = bool(int(line[2]))
                            time = int(line[3])
                            block_size = 0 if line[4].startswith("LLL") else int(line[4][4:])
                            info = int(line[5])
                            liars = int(line[6])
                            real_info = int(line[7])
                            bad_info = int(line[8])
                            good_info = int(line[9])
                            liar_positions = None
                            if len(line) >= 11:
                                liar_positions = line[10]
                            normdist = None
                            if len(line) >= 12:
                                normdist = float(line[11])
                            row = None
                            if len(line) >= 13:
                                row = int(line[12])
                            run = AttackRun(data_type, bound_type, method_type, recenter, c, n, d, n_seed, d_seed, success, time, block_size, info, liars, real_info, bad_info, good_info, liar_positions, normdist, row)
                            runs.add(run)
                        except:
                            continue
    return runs


def save_transformed(all_runs, fname):
    with open(fname, "wb") as f:
        pickle.dump(all_runs, f)


def load_transformed(fname):
    if not exists(fname):
        return set()
    with open(fname, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    all_runs = load_transformed("results/runs.pickle")
    d_list = list(range(50, 142, 2))
    n_list = list(it.chain(range(500, 7100, 100), range(8000, 11000, 1000)))
    for data in ("sw", "card", "sim", "tpm"):
        for bounds in ("known", "knownre", "geom", "geom1", "geom2", "geom3", "geom4", "geomN", "const1", "const2", "const3", "const4", "template01", "template10", "template30", "templatem01", "templatem10", "templatem30"):
            for method in ("svp", "np", "round", "sieve"):
                for recenter in ("yes", "no"):
                    for c in ("1.5", "1"):
                        loaded = load_data(data, bounds, method, recenter, c, d_list, n_list)
                        all_runs.update(loaded)
                        if loaded:
                            print(data, bounds, method, recenter, c, len(loaded))
                            print(len(all_runs))
    save_transformed(all_runs, "results/runs.pickle")