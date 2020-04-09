#!/usr/bin/env python
import argparse
import itertools as it
from copy import copy
from math import sqrt, ceil
import re

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm, gridspec
from matplotlib.colors import Normalize
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter)

from join import load_transformed, AttackRun

d_list = list(range(50, 142, 2))
n_list = list(it.chain(range(500, 7100, 100), range(8000, 11000, 1000)))


def get_gridspec(datas, grid):
    if grid is None:
        w = ceil(sqrt(len(datas)))
        if len(datas) == 2:
            gs = gridspec.GridSpec(2, 1)
        else:
            gs = gridspec.GridSpec(w, w)
    else:
        gs = gridspec.GridSpec(*grid)
    return gs


def reshape_grid(x, y, z, n_list, d_list):
    X, Y = np.meshgrid(n_list, d_list)
    zs = np.array(z)
    Z = zs.reshape(X.shape, order="F")
    return X, Y, Z


def sync_viewing(axes, fig):
    def on_move(event):
        for ax in axes:
            if event.inaxes == ax:
                break
        else:
            return

        for axx in axes:
            if axx != ax:
                if ax.button_pressed in ax._rotate_btn:
                    axx.view_init(elev=ax.elev, azim=ax.azim)
                elif ax.button_pressed in ax._zoom_btn:
                    axx.set_xlim3d(ax.get_xlim3d())
                    axx.set_ylim3d(ax.get_ylim3d())
                    axx.set_zlim3d(ax.get_zlim3d())
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)


def remap(vals, default, ns=n_list, ds=d_list):
    N = []
    D = []
    V = []
    for n in ns:
        for d in ds:
            N.append(n)
            D.append(d)
            key = (n, d)
            if key in vals:
                V.append(vals[key])
            else:
                V.append(default)
    return N, D, V


def map2success(data):
    vals = {}
    min_n = None
    for run in data:
        key = (run.N, run.d)
        vals.setdefault(key, 0)
        if run.success:
            vals[key] += 1
            if min_n is None or min_n > run.N:
                min_n = run.N
    N, D, S = remap(vals, 0)
    return N, D, S, min_n


def map2normdist(data):
    vals = {}
    cnts = {}
    for run in data:
        key = (run.N, run.d)
        vals.setdefault(key, 0)
        cnts.setdefault(key, 0)
        if run.success and run.normdist is not None:
            vals[key] += run.normdist
            cnts[key] += 1
    for key in vals:
        if cnts[key] != 0:
            vals[key] /= cnts[key]
    N, D, S = remap(vals, 0)
    return N, D, S, None

def map2row(data):
    vals = {}
    cnts = {}
    for run in data:
        key = (run.N, run.d)
        vals.setdefault(key, 0)
        cnts.setdefault(key, 0)
        if run.success and run.row is not None:
            vals[key] += run.row
            cnts[key] += 1
    for key in vals:
        if cnts[key] != 0:
            vals[key] /= cnts[key]
    N, D, S = remap(vals, 0)
    return N, D, S, None

def map2runs(data):
    vals = {}
    for run in data:
        key = (run.N, run.d)
        vals.setdefault(key, 0)
        vals[key] += 1
    N, D, R = remap(vals, 0)
    return N, D, R, None

def _map2single(data, attr):
    vals = {}
    cnts = {}
    for run in data:
        key = (run.N, run.d)
        vals.setdefault(key, 0)
        cnts.setdefault(key, 0)
        vals[key] += getattr(run, attr)
        cnts[key] += 1
    for key in vals:
        if cnts[key] != 0:
            vals[key] /= cnts[key]
    N, D, V = remap(vals, 0)
    return N, D, V, None


def map2liars(data):
    return _map2single(data, "liars")

def map2info(data):
    return _map2single(data, "info")

def map2realinfo(data):
    return _map2single(data, "real_info")

def map2goodinfo(data):
    return _map2single(data, "good_info")

def map2badinfo(data):
    return _map2single(data, "bad_info")

def map2success_avg(data):
    res = {n: 0 for n in n_list}
    cnts = {n: 0 for n in n_list}
    for run in data:
        cnts[run.N] += 1
        if run.success:
            res[run.N] += 1
    for n in n_list:
        if cnts[n] != 0:
            res[n] /= cnts[n]
    return [res[n] for n in n_list]


def map2liarpos(data, dim):
    liar_indices = [0 for _ in range(dim)]
    count = 0
    for run in data:
        if run.d == dim:
            count += 1
            liar_positions = run.liar_positions
            if liar_positions:
                liars = liar_positions.split(";")
                for liar in liars:
                    i = int(liar.split("@")[0])
                    liar_indices[i] += 1
    if count != 0:
        liar_indices = [i/count for i in liar_indices]
    return liar_indices


def map2liarpos_heat(data):
    vals = {}
    cnts = {}
    for run in data:
        cnts.setdefault(run.d, 0)
        cnts[run.d] += 1
        if run.liar_positions:
            liars = run.liar_positions.split(";")
            for liar in liars:
                i = int(liar.split("@")[0])
                key = (run.d, i)
                vals.setdefault(key, 0)
                vals[key] += 1
    for key in vals:
        if cnts[key[0]] != 0:
            vals[key] /= cnts[key[0]]
    N, D, V = remap(vals, 0, d_list, list(range(0, 50, 2)) + d_list)
    return N, D, V, None


def map2liardepth(data, dim):
    liar_indices = [0 for _ in range(dim)]
    liar_counts = [0 for _ in range(dim)]
    for run in data:
        if run.d == dim:
            liar_positions = run.liar_positions
            if liar_positions:
                liars = liar_positions.split(";")
                for liar in liars:
                    i, j = liar.split("@")
                    i = int(i)
                    j = int(j)
                    liar_indices[i] += j
                    liar_counts[i] += 1
    for i in range(dim):
        if liar_counts[i] != 0:
            liar_indices[i] /= liar_counts[i]
    return liar_indices

def map2liardepth_heat(data):
    vals = {}
    cnts = {}
    for run in data:
        if run.liar_positions:
            liars = run.liar_positions.split(";")
            for liar in liars:
                i, j = liar.split("@")
                i = int(i)
                j = int(j)
                key = (run.d, i)
                vals.setdefault(key, 0)
                cnts.setdefault(key, 0)
                vals[key] += j
                cnts[key] += 1
    for key in vals:
        if cnts[key] != 0:
            vals[key] /= cnts[key]
    N, D, V = remap(vals, 0, d_list, list(range(0, 50, 2)) + d_list)
    return N, D, V, None

def map2liarinfo(data, dim):
    liar_indices = [0 for _ in range(dim)]
    count = 0
    for run in data:
        if run.d == dim:
            count += 1
            liar_positions = run.liar_positions
            if liar_positions:
                liars = liar_positions.split(";")
                for liar in liars:
                    i, j = liar.split("@")
                    i = int(i)
                    j = int(j)
                    liar_indices[i] += j
    if count != 0:
        liar_indices = [i/count for i in liar_indices]
    return liar_indices

def map2liarinfo_heat(data):
    vals = {}
    cnts = {}
    for run in data:
        cnts.setdefault(run.d, 0)
        cnts[run.d] += 1
        if run.liar_positions:
            liars = run.liar_positions.split(";")
            for liar in liars:
                i, j = liar.split("@")
                i = int(i)
                j = int(j)
                key = (run.d, i)
                vals.setdefault(key, 0)
                vals[key] += j
    for key in vals:
        if cnts[key[0]] != 0:
            vals[key] /= cnts[key[0]]
    N, D, V = remap(vals, 0, d_list, list(range(0, 50, 2)) + d_list)
    return N, D, V, None

def map2blocks(data):
    vals = {}
    cnts = {}
    for run in data:
        key = (run.N, run.d)
        vals.setdefault(key, 0)
        cnts.setdefault(key, 0)
        if run.success:
            vals[key] += run.block_size
            cnts[key] += 1
    for key in vals:
        if cnts[key] != 0:
            vals[key] /= cnts[key]
    N, D, B = remap(vals, 0)
    return N, D, B, None


def map2runtime(data):
    vals = {}
    cnts = {}
    for run in data:
        key = (run.N, run.d)
        vals.setdefault(key, 0)
        cnts.setdefault(key, 0)
        if run.success:
            vals[key] += run.time
            cnts[key] += 1
    for key in vals:
        if cnts[key] != 0:
            vals[key] /= cnts[key]
    N, D, R = remap(vals, 0)
    return N, D, R, None


def plot_todim(datas, fig, map_func, ylabel):
    ax = fig.add_subplot(111)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Dimension of matrix (D)")
    for name, data in sorted(datas.items()):
        value = map_func(data)
        ax.plot(d_list, value, label=name)
    ax.legend()


def plot_toN(datas, fig, map_func, ylabel):
    ax = fig.add_subplot(111)
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(MultipleLocator(1000))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(MultipleLocator(100))
    ax.set_xlabel("Number of signatures (N)")
    for name, data in sorted(datas.items()):
        value = map_func(data)
        ax.plot(n_list, value, label=name)
    ax.legend()


def plot_dim(datas, fig, map_func, dim, ylabel):
    ax = fig.add_subplot(111)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Index")
    for name, data in sorted(datas.items()):
        value = map_func(data, dim)
        ax.plot(range(dim), value, label=name)
    ax.legend()


def plot_heatmap(datas, fig, map_func, zlabel, flat=True, grid=None, ns=n_list, ds=d_list, xlabel="Number of signatures (N)", ylabel="Dimension of matrix (D)"):
    gs = get_gridspec(datas, grid)
    i = 0
    axes = []
    for name, data in sorted(datas.items()):
        if flat:
            ax = fig.add_subplot(gs[i])
        else:
            ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        x, y, z, min_n = map_func(data)
        X, Y, Z = reshape_grid(x, y, z, ns, ds)
        cmap = copy(cm.get_cmap("viridis"))
        cmap.set_under("black")
        #norm = Normalize(vmin=0.0001)
        norm = None
        if flat:
            im = ax.pcolormesh(X, Y, Z, cmap=cmap, norm=norm)
            if min_n is not None:
                ax.axvline(x=min_n, label="{}".format(min_n), color="red")
            fig.colorbar(im)
        else:
            ax.plot_surface(X, Y, Z, cmap=cmap, norm=norm)
            ax.set_zlabel(zlabel)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(name)
        i += 1
    if not flat:
        sync_viewing(axes, fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--figsize", type=str, default="7x4")
    parser.add_argument("--grid", type=str)
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--bounds", type=str, required=True)
    parser.add_argument("--methods", type=str, required=True)
    parser.add_argument("--diff", type=str, required=True)
    parser.add_argument("--flat", action="store_true")
    parser.add_argument("figure", type=str)

    args = parser.parse_args()
    figsize = tuple(map(float, args.figsize.split("x")))
    grid = tuple(map(int, args.grid.split("x"))) if args.grid else None
    data_types = args.data.split(",")
    bound_types = args.bounds.split(",")
    method_types = args.methods.split(",")
    diff = args.diff.split(",")
    figure = args.figure

    runs = load_transformed("results/runs.pickle")
    fig = plt.figure(figsize=figsize)
    datas = {}
    for run in runs:
        if run.dataset in data_types and run.bounds in bound_types and run.method in method_types and run.diff in diff:
            s = datas.setdefault("_".join((run.dataset, run.bounds, run.method, run.diff)), set())
            s.add(run)
    if figure == "success":
        plot_heatmap(datas, fig, map2success, "Successes (out of 5)", flat=args.flat, grid=grid)
    elif figure == "normdist":
        plot_heatmap(datas, fig, map2normdist, "Normdist", flat=args.flat, grid=grid)
    elif figure == "row":
        plot_heatmap(datas, fig, map2row, "Row", flat=args.flat, grid=grid)
    elif figure == "blocks":
        plot_heatmap(datas, fig, map2blocks, "Block size", flat=args.flat, grid=grid)
    elif figure == "runtime":
        plot_heatmap(datas, fig, map2runtime, "Runtime (s)", flat=args.flat, grid=grid)
    elif figure == "runs":
        plot_heatmap(datas, fig, map2runs, "Total runs", flat=args.flat, grid=grid)
    elif figure == "liars":
        plot_heatmap(datas, fig, map2liars, "Liars", flat=args.flat, grid=grid)
    elif figure == "info":
        plot_heatmap(datas, fig, map2info, "info", flat=args.flat, grid=grid)
    elif figure == "goodinfo":
        plot_heatmap(datas, fig, map2goodinfo, "good info", flat=args.flat, grid=grid)
    elif figure == "badinfo":
        plot_heatmap(datas, fig, map2badinfo, "bad info", flat=args.flat, grid=grid)
    elif figure == "realinfo":
        plot_heatmap(datas, fig, map2realinfo, "real info", flat=args.flat, grid=grid)
    elif figure == "success_avg":
        plot_toN(datas, fig, map2success_avg, "Successes")
    elif figure == "liarpos":
        plot_heatmap(datas, fig, map2liarpos_heat, "liar amount", flat=args.flat, grid=grid, ns=d_list, ds=list(range(0, 50, 2)) + d_list, xlabel="run.D", ylabel="D")
    elif figure == "liardepth":
        plot_heatmap(datas, fig, map2liardepth_heat, "liar depth(average)", flat=args.flat, grid=grid, ns=d_list, ds=list(range(0, 50, 2)) + d_list, xlabel="run.D", ylabel="D")
    elif figure == "liarinfo":
        plot_heatmap(datas, fig, map2liarinfo_heat, "liar info", flat=args.flat, grid=grid, ns=d_list, ds=list(range(0, 50, 2)) + d_list, xlabel="run.D", ylabel="D")
    elif dim_match := re.match("liarpos\(([0-9]+)\)", figure):
        plot_dim(datas, fig, map2liarpos, int(dim_match.group(1)), "liar amount")
    elif dim_match := re.match("liardepth\(([0-9]+)\)", figure):
        plot_dim(datas, fig, map2liardepth, int(dim_match.group(1)), "liar depth (average)")
    elif dim_match := re.match("liarinfo\(([0-9]+)\)", figure):
        plot_dim(datas, fig, map2liarinfo, int(dim_match.group(1)), "liar info")
    else:
        print("Unknown figure.")
        exit(1)
    fig.tight_layout()
    plt.show()
