#!/usr/bin/env python
import json
import csv
import re
import numpy as np
import random

from os import path


def const_bound_func(bounds):
    return bounds["value"]

def geom_bound_func(index, dim, bounds):
    max_bound = 0
    for part, bound in bounds["parts"].items():
        if index < dim / int(part) and max_bound < bound:
            max_bound = bound
    return max_bound

def geomN_bound_func(index, N, bounds):
    if "index" in bounds:
        index += bounds["index"]
    value = bounds["value"] if "value" in bounds else 0
    mul = bounds["multiple"] if "multiple" in bounds else 1
    i = 1
    while (N * mul) / (2 ** i) >= index + 1:
        i += 1
    i -= 1
    if i <= 1:
        return 0
    return max(i - value, 0)

def const_bounds(params, N, d):
    return [const_bound_func(params) for i in range(d)]

def geom_bounds(params, N, d):
    return [geom_bound_func(i, d, params) for i in range(d)]

def geomN_bounds(params, N, d):
    return [geomN_bound_func(i, N, params) for i in range(d)]

def template_bounds(params, N, d):
    bounds = [0 for _ in range(d)]
    for k, v in params.items():
        for i in range(*v):
            bounds[i] = 256 - int(k)
    return bounds

def create_bounds(data_type, bound_type, N, d):
    if bound_type.startswith("const"):
        params = {"value": int(bound_type[5:])}
        return const_bounds(params, N, d)
    elif bound_type.startswith("geomN"):
        params = {}
        if imatch := re.search("i[0-9]+", bound_type):
            params["index"] = int(imatch.group(0)[1:])
        if mmatch := re.search("m[0-9]+", bound_type):
            params["value"] = int(mmatch.group(0)[1:])
        if xmatch := re.search("x[0-9]+", bound_type):
            params["multiple"] = int(xmatch.group(0)[1:]) /100
        return geomN_bounds(params, N, d)
    elif bound_type.startswith("geom"):
        bound = int(bound_type[4:])
        p1 = bound
        p2 = bound + 1
        p4 = bound + 2
        p8 = bound + 3
        p16 = bound + 4
        p32 = bound + 5
        p64 = bound + 6
        p128 = bound + 7
        params = {
            "parts": {
                "128": p128,
                "64": p64,
                "32": p32,
                "16": p16,
                "8": p8,
                "4": p4,
                "2": p2,
                "1": p1
            }
        }
        return geom_bounds(params, N, d)

def load_data(data_type):
    if data_type == "sim":
        fname = "time_sim.csv"
    elif data_type == "sw":
        fname = "time_gcrypt.csv"
    elif data_type == "card":
        fname = "time_athena.csv"
    elif data_type == "tpm":
        fname = "time_tpmfail_stm.csv"
    else:
        raise ValueError
    with open(path.join("..", "..", "data", fname), "r") as f:
        reader = csv.reader(f)
        lines = [(int(line[0]), int(line[1])) for line in reader]
    return lines

def simulate(lines, N, d, bounds, c):
    n = 2
    m = 500
    cd_errors = []
    cd_info = []
    for cd in range(d, int(c * d) + 1):
        min_errs = None
        errors = []
        infos = []
        for i in range(n):
            print(".", end="", flush=True)
            N_sample = random.sample(lines, N)
            N_sorted = list(sorted(N_sample))
            cd_sample = N_sorted[:cd]
            for j in range(m):
                d_sample = list(map(lambda x: x[1], sorted(random.sample(cd_sample, d))))
                errs = 0
                info = 0
                for bound, real in zip(bounds, d_sample):
                    if real < bound:
                        errs += 1
                    else:
                        info += bound
                errors.append(errs)
                infos.append(info)
        cd_errors.append(np.mean(errors))
        cd_info.append(np.mean(info))
        
    return range(d, int(c * d) + 1), cd_errors, cd_info
            

def estimate_residuals(lines, N, d, bounds):
    n = 1000
    residuals = [[] for _ in range(d)]
    for i in range(n):
        N_sample = random.sample(lines, N)
        N_sorted = list(sorted(N_sample))
        lattice = list(map(lambda x: x[1], N_sorted[:d]))
        j = 0
        for bound, real in zip(bounds, lattice):
            residuals[j].append(bound - real)
            j += 1
    return residuals


if __name__ == "__main__":
    import argparse
    import matplotlib.pyplot as plt
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--bounds", type=str, required=True)
    parser.add_argument("N", type=int)
    parser.add_argument("d", type=int)

    args = parser.parse_args()
    data_types = args.data.split(",")
    bound_types = args.bounds.split(",")
    fig = plt.figure()
    ax = fig.add_subplot()

    for data_type in sorted(data_types):
        lines = load_data(data_type)
        for bound_type in sorted(bound_types):
            bounds = create_bounds(data_type, bound_type, args.N, args.d)
            x, errors, info = simulate(lines, args.N, args.d, bounds, 4)
            ax.plot(x, errors, label="_".join((data_type, bound_type)) + " errors")
            ax.plot(x, info, label="_".join((data_type, bound_type)) + " info")
    ax.axhline(y=0, color="black", lw=2)
    ax.legend()
    plt.show()
    