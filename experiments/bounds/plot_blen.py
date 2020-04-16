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
    elif bound_type.startswith("template"):
        with open(f"templates_{data_type}.json", "r") as f:
            temp = json.load(f)
        i = int(bound_type[8:])
        f = f"{i / 100:.2f}".rstrip("0")
        return template_bounds(temp[f][str(d)][str(N)], N, d)

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

def create_real(lines, N, d):
    N_sample = random.sample(lines, N)
    N_sorted = list(sorted(N_sample))
    #N_sorted = N_sample
    lattice = N_sorted[:d]
    return list(map(lambda x: x[1], lattice))

def estimate_errors(lines, N, d, bounds):
    n = 1000
    total = []
    for i in range(n):
        N_sample = random.sample(lines, N)
        N_sorted = list(sorted(N_sample))
        lattice = list(map(lambda x: x[1], N_sorted[:d]))
        errors = 0
        for bound, real in zip(bounds, lattice):
            if bound > real:
                errors += 1
        total.append(errors)
    return np.mean(total), np.std(total)

def estimate_residuals(lines, N, d, bounds):
    n = 1000
    residuals = [[] for _ in range(d)]
    for i in range(n):
        N_sample = random.sample(lines, N)
        N_sorted = list(sorted(N_sample))
        lattice = list(map(lambda x: x[1], N_sorted[:d]))
        j = 0
        for bound, real in zip(bounds, lattice):
            residuals[j].append(real - bound)
            j += 1
    return residuals

def estimate_blens(lines, N, d, i):
    n = 5000
    return [create_real(lines, N, d)[i] for _ in range(n)]

if __name__ == "__main__":
    import argparse
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator
    from matplotlib import cm
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--bounds", type=str, required=True)
    parser.add_argument("N", type=int)
    parser.add_argument("d", type=int)
    parser.add_argument("i", type=int)

    #plt.style.use("bmh")
    cm = cm.get_cmap("tab10")

    args = parser.parse_args()
    data_types = args.data.split(",")
    bound_types = args.bounds.split(",")
    fig = plt.figure(figsize=(11,3.6), dpi=120)
    ax = fig.add_subplot()
    for data_type in sorted(data_types):
        lines = load_data(data_type)
        blens = estimate_blens(lines, args.N, args.d, args.i)
        h = ax.hist(blens, bins=max(blens) - min(blens), histtype="step", align="left", label=data_type)
        for bound_type in sorted(bound_types):
            bounds = create_bounds(data_type, bound_type, args.N, args.d)
            ax.axvline(x=bounds[args.i], color="black", label=" ".join((data_type, bound_type)))
    # for data_type in sorted(data_types):
        # lines = load_data(data_type)
        # bounds = create_real(lines, args.N, args.d)
        # data[data_type] = lines
        # ax.step(range(args.d), bounds, label=data_type, where="post", linestyle=":", color=cm(0/10)) # + f" ({sum(bounds)}b)"
        # if max(bounds) > max_bound:
            # max_bound = max(bounds)
    # 
    # for data_type in sorted(data_types):
        # for bound_type in sorted(bound_types):
            # bounds = create_bounds(data_type, bound_type, args.N, args.d)
            # mean_err, std_err = estimate_errors(data[data_type], args.N, args.d, bounds)
            # residuals = estimate_residuals(data[data_type], args.N, args.d, bounds)
            # ax.boxplot(residuals, manage_ticks=False)
            # mean_residuals = [np.mean(residual) for residual in residuals]
            # ax.plot(range(args.d), mean_residuals, label=" - ".join((data_type, bound_type)) + f" residuals", linestyle="--", color=cm(1/10)) #  ({np.mean(mean_residuals):.2f})
            # 
            # ax.step(range(args.d), bounds, label=bound_type, where="post", color=cm(2/10)) #  + f" ({sum(bounds)}b) ({mean_err:.2f}e, {std_err:.2f})"
            # if max(bounds) > max_bound:
                # max_bound = max(bounds)
    # ax.axhline(y=0, color="black", lw=2)
    # ax.legend()
    # #ax.set_ylim((0, max_bound + 1))
    # ax.set_xlabel("index")
    # ax.set_ylabel("bound")
    # ax.set_xticks(list(range(0, args.d + 10, 10)))
    # #ax.set_xticks([0,10,20,30,40,50,60,70,80,90,100])
    # #ax.xaxis.set_major_locator(MultipleLocator())
    ax.legend()
    plt.show()
    