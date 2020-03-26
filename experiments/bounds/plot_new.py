#!/usr/bin/env python
import argparse
import itertools as it
from math import sqrt, ceil

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm, gridspec
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter)

from join import load_transformed, AttackRun

d_list = list(range(50, 142, 2))
n_list = list(it.chain(range(500, 7100, 100), range(8000, 11000, 1000)))


def get_gridspec(datas):
    w = ceil(sqrt(len(datas)))
    if len(datas) == 2:
        gs = gridspec.GridSpec(2, 1)
    else:
        gs = gridspec.GridSpec(w, w)
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


def remap(vals, default):
    N = []
    D = []
    V = []
    for n in n_list:
        for d in d_list:
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
        if run.success:
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
        if run.success:
            vals[key] += run.row
            cnts[key] += 1
    for key in vals:
        if cnts[key] != 0:
            vals[key] /= cnts[key]
    N, D, S = remap(vals, 0)
    return N, D, S, None


def map2liars(data):
    vals = {}
    cnts = {}
    for run in data:
        key = (run.N, run.d)
        vals.setdefault(key, 0)
        cnts.setdefault(key, 0)
        vals[key] += run.liars
        cnts[key] += 1
    for key in vals:
        if cnts[key] != 0:
            vals[key] /= cnts[key]
    N, D, S = remap(vals, 0)
    return N, D, S, None


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
    for run in data:
        if run.d == dim:
            liar_positions = run.liar_positions
            if liar_positions:
                liars = liar_positions.split(";")
                for liar in liars:
                    i = int(liar.split("@")[0])
                    liar_indices[i] += 1
    return liar_indices


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
    for name, data in datas.items():
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
    for name, data in datas.items():
        value = map_func(data)
        ax.plot(n_list, value, label=name)
    ax.legend()


def plot_dim(datas, fig, map_func, dim, ylabel):
    ax = fig.add_subplot(111)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Index")
    for name, data in datas.items():
        value = map_func(data, dim)
        ax.plot(range(dim), value, label=name)
    ax.legend()


def plot_heatmap(datas, fig, map_func, zlabel, flat=True):
    gs = get_gridspec(datas)
    i = 0
    axes = []
    for name, data in datas.items():
        if flat:
            ax = fig.add_subplot(gs[i])
        else:
            ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        x, y, z, min_n = map_func(data)
        X, Y, Z = reshape_grid(x, y, z, n_list, d_list)
        if flat:
            ax.pcolormesh(X, Y, Z, cmap=cm.get_cmap("viridis"))
            if min_n is not None:
                ax.axvline(x=min_n, label="{}".format(min_n), color="red")
        else:
            ax.plot_surface(X, Y, Z, cmap=cm.get_cmap("viridis"))
            ax.set_zlabel(zlabel)
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_title(name)
        i += 1
    if not flat:
        sync_viewing(axes, fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--figsize", type=str, default="7x4")
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--bounds", type=str, required=True)
    parser.add_argument("--flat", action="store_true")

    args = parser.parse_args()
    figsize = tuple(map(float, args.figsize.split("x")))
    data_types = args.data.split(",")
    bound_types = args.bounds.split(",")

    runs = load_transformed("runs.pickle")
    fig = plt.figure(figsize=figsize)
    datas = {}
    for run in runs:
        if run.dataset in data_types and run.bounds in bound_types:
            s = datas.setdefault(run.dataset + "_" + run.bounds, set())
            s.add(run)
    # plot_heatmap(datas, fig, map2success, "Successes (out of 5)", flat=args.flat)
    # plot_heatmap(datas, fig, map2normdist, "Normdist", flat=args.flat)
    # plot_heatmap(datas, fig, map2row, "Row", flat=args.flat)
    # plot_heatmap(datas, fig, map2liars, "Liars", flat=args.flat)
    # plot_toN(datas, fig, map2success_avg, "Successes")
    plot_dim(datas, fig, map2liarpos, 140, "liar amount")
    fig.tight_layout()
    plt.show()
