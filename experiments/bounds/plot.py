#!/usr/bin/env python

import argparse
import matplotlib.pyplot as plt
from matplotlib import cm, gridspec
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import Normalize
import itertools as it
from os.path import exists
import csv
import numpy as np
from copy import copy
from math import sqrt, ceil

from matplotlib.colors import ListedColormap, LinearSegmentedColormap, DivergingNorm
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)

from .join import load_transformed

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
    Z = zs.reshape(X.shape)
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


def plot_1(datas, d_list, n_list, fig):
    fig.suptitle("Success rate.", fontweight="bold")
    def map2success(data):
        N = []
        D = []
        S = []
        min_n = None
        for d, n, runs in data:
            s = 0
            for run in runs:
                s += run.success
            if s != 0 and (min_n is None or min_n > n):
                min_n = n
            N.append(n)
            D.append(d)
            S.append(s)
        return N, D, S, min_n
    gs = get_gridspec(datas)
    i = 0
    axes = []
    for name, data in datas:
        ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        x, y, z, min_n = map2success(data)
        X, Y, Z = reshape_grid(x, y, z, n_list, d_list)
    
        ax.plot_surface(X, Y, Z, cmap=cm.viridis)
        ax.set_xlabel("Number of signatures (N)\nmin(N) = {}".format(min_n))
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_zlabel("Successes (out of 5)")
        ax.set_title(name)
        i += 1
    sync_viewing(axes, fig)


def plot_2_const(datas, d_list, n_list, fig):
    #fig.suptitle("Success rate (over all dimensions).", fontweight="bold")
    def map2allsuccess(data):
        NS = {}
        for d, n, runs in data:
            s = NS.setdefault(n, 0)
            for run in runs:
                s += run.success
            NS[n] = s
        return list(NS.keys()), list(NS.values())

    ax = fig.add_subplot(111)
    max_s = len(d_list) * 5
    i = 0
    #marks = "ox+ds^"
    marks = {
        "const2": "",
        "const3": "",
        "const4": ""
    }
    lines = {
        "const2": ":",
        "const3": "--",
        "const4": "-."
    }
    cm = plt.get_cmap("tab20c")
    colors = {
        "const2": 0/20,
        "const3": 1/20,
        "const4": 2/20
    }
    names = {
        "const2": "const(3)",
        "const3": "const(4)",
        "const4": "const(5)"
    }
    for name, data in datas:
        dname, bname = name.split("_")
        if dname == "sim":
            color = "red"
            base = 0
        elif dname == "sw":
            color = "green"
            base = 4/20
        elif dname == "card":
            color = "blue"
            base = 8/20
        x, y = map2allsuccess(data)
        ax.plot(x, [s / max_s for s in y], linestyle=lines[bname], label="{} {}".format(dname, names[bname]), color=cm(base+colors[bname]), marker=marks[bname])
        i += 1
    ax.set_xlabel("Number of signatures (N)")
    ax.set_ylabel("Success rate")
    ax.legend(prop={"size": 6})
    ax.xaxis.set_major_locator(MultipleLocator(1000))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(MultipleLocator(100))


def plot_2(datas, d_list, n_list, fig):
    #fig.suptitle("Success rate (over all dimensions).", fontweight="bold")
    def map2allsuccess(data):
        NS = {}
        for d, n, runs in data:
            s = NS.setdefault(n, 0)
            for run in runs:
                s += run.success
            NS[n] = s
        return list(NS.keys()), list(NS.values())

    ax = fig.add_subplot(111)
    max_s = len(d_list) * 5
    i = 0
    #marks = "ox+ds^"
    marks = {
        "geom1": "",
        "geom": "",
        "geom3": "",
        "geom4": ""
    }
    lines = {
        "geom1": ":",
        "geom": "--",
        "geom3": "-.",
        "geom4": "-"
    }
    cm = plt.get_cmap("tab20c")
    colors = {
        "geom1": 0/20,
        "geom": 1/20,
        "geom3": 2/20,
        "geom4": 3/20
    }
    names = {
        "geom1": "geom(2)",
        "geom": "geom(3)",
        "geom3": "geom(4)",
        "geom4": "geom(5)"
    }
    for name, data in datas:
        dname, bname = name.split("_")
        if dname == "sim":
            color = "red"
            base = 0
        elif dname == "sw":
            color = "green"
            base = 4/20
        elif dname == "card":
            color = "blue"
            base = 8/20
        x, y = map2allsuccess(data)
        ax.plot(x, [s / max_s for s in y], linestyle=lines[bname], label="{} {}".format(dname, names[bname]), color=cm(base+colors[bname]), marker=marks[bname])
        i += 1
    ax.set_xlabel("Number of signatures (N)")
    ax.set_ylabel("Success rate")
    ax.legend(prop={"size": 6})
    ax.xaxis.set_major_locator(MultipleLocator(1000))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(MultipleLocator(100))


def plot_2_template(datas, d_list, n_list, fig):
    #fig.suptitle("Success rate (over all dimensions).", fontweight="bold")
    def map2allsuccess(data):
        NS = {}
        for d, n, runs in data:
            s = NS.setdefault(n, 0)
            for run in runs:
                s += run.success
            NS[n] = s
        return list(NS.keys()), list(NS.values())

    ax = fig.add_subplot(111)
    max_s = len(d_list) * 5
    i = 0
    #marks = "ox+ds^"
    lines = {
        "template10": "--",
        "template30": "-.",
        "templatem10": "--",
        "templatem30": "-."
    }
    cm = plt.get_cmap("tab20c")
    colors = {
        "template10": 0/20,
        "template30": 1/20,
        "templatem10": 2/20,
        "templatem30": 3/20
    }
    names = {
        "template10": "alpha = 0.10 (+1)",
        "template30": "alpha = 0.30 (+1)",
        "templatem10": "alpha = 0.10",
        "templatem30": "alpha = 0.30"
    }
    for name, data in datas:
        dname, bname = name.split("_")
        if dname == "sim":
            color = "red"
            base = 0
        elif dname == "sw":
            color = "green"
            base = 4/20
        elif dname == "card":
            color = "blue"
            base = 8/20
        x, y = map2allsuccess(data)
        ax.plot(x, [s / max_s for s in y], linestyle=lines[bname], label="{} {}".format(dname, names[bname]), color=cm(base+colors[bname]))
        i += 1
    ax.set_xlabel("Number of signatures (N)")
    ax.set_ylabel("Success rate")
    ax.legend(prop={"size": 6})
    ax.xaxis.set_major_locator(MultipleLocator(1000))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(MultipleLocator(100))


def plot_3(datas, d_list, n_list, fig):
    fig.suptitle("Average block size in successful runs.", fontweight="bold")
    def map2blocks(data):
        N = []
        D = []
        B = []
        for d, n, runs in data:
            blocks = 0
            successes = 0
            for run in runs:
                if run.success:
                    blocks += run.block_size
                    successes += 1
            if successes != 0:
                b = blocks / successes
            else:
                b = 0
            N.append(n)
            D.append(d)
            B.append(b)
        return N, D, B
    gs = get_gridspec(datas)
    i = 0
    axes = []
    for name, data in datas:
        ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        x, y, z = map2blocks(data)
        X, Y, Z = reshape_grid(x, y, z, n_list, d_list)
        cmap = copy(cm.viridis)
        cmap.set_under("black")
        norm = Normalize(vmin=0.0001)
    
        ax.plot_surface(X, Y, Z, cmap=cmap, norm=norm)
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_zlabel("Average block size")
        ax.set_title(name)
        i += 1
    sync_viewing(axes, fig)


def plot_4(datas, d_list, n_list, fig):
    fig.suptitle("Average number of liars.", fontweight="bold")
    def map2liars(data):
        N = []
        D = []
        L = []
        for d, n, runs in data:
            l = 0
            for run in runs:
                l += run.liars
            if runs:
                l /= len(runs)
            N.append(n)
            D.append(d)
            L.append(l)
        return N, D, L
    gs = get_gridspec(datas)
    i = 0
    axes = []
    for name, data in datas:
        ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        x, y, z = map2liars(data)
        X, Y, Z = reshape_grid(x, y, z, n_list, d_list)
    
        ax.plot_surface(X, Y, Z, cmap=cm.viridis)
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_zlabel("Average number of liars")
        ax.set_title(name)
        i += 1
    sync_viewing(axes, fig)


def plot_4_flat(datas, d_list, n_list, fig):
    #fig.suptitle("Average number of liars.", fontweight="bold")
    def map2liars(data):
        N = []
        D = []
        L = []
        for d, n, runs in data:
            l = 0
            for run in runs:
                l += run.liars
            if runs:
                l /= len(runs)
            N.append(n)
            D.append(d)
            L.append(l)
        return N, D, L
    gs = get_gridspec(datas)
    #gs = gridspec.GridSpec(3, 1)
    i = 0
    axes = []
    max_l = 0
    for name, data in datas:
        x, y, z = map2liars(data)
        if max(z) > max_l:
            max_l = max(z)
    viridis = cm.get_cmap('viridis', max_l)
    print(max_l)
    newcolors = viridis(np.linspace(0, 1, max_l))
    pink = np.array([248/256, 24/256, 148/256, 1])
    newcolors[:10, :] = pink
    newcmp = ListedColormap(newcolors)
    divnorm = DivergingNorm(vmin=0, vcenter=6, vmax=max_l)
    cmap = cm.get_cmap("RdBu", max_l/2)
    
    for name, data in datas:
        ax = fig.add_subplot(gs[i])
        axes.append(ax)
        x, y, z = map2liars(data)
        n_list = list(range(500, 7100, 100))
        Z = np.empty((len(d_list), len(n_list)))
        for n, d, s in zip(x, y, z):
            if n < 8000:
                Z[d_list.index(d), n_list.index(n)] = s

        im = ax.imshow(Z, aspect="auto", interpolation="nearest", norm=divnorm, cmap=cmap, extent=(min(n_list), max(n_list), min(d_list), max(d_list)), origin="low")
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_title(name.split("_")[0])
        i += 1
    #fig.subplots_adjust(top=0.965,bottom=0.065,left=0.110,right=0.845)
    fig.subplots_adjust(right=0.8)
    cbar_ax = fig.add_axes([0.90, 0.05, 0.05, 0.9])
    #fig.colorbar(im, cax=cbar_ax)
    fig.colorbar(cm.ScalarMappable(norm=divnorm, cmap=cmap), cax=cbar_ax)

    
def plot_5(datas, d_list, n_list, fig):
    fig.suptitle("Average good info.", fontweight="bold")
    def map2goodinfo(data):
        N = []
        D = []
        I = []
        for d, n, runs in data:
            i = 0
            for run in runs:
                i += run.good_info
            if runs:
                i /= len(runs)
            N.append(n)
            D.append(d)
            I.append(i)
        return N, D, I
    gs = get_gridspec(datas)
    i = 0
    axes = []
    for name, data in datas:
        ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        x, y, z = map2goodinfo(data)
        X, Y, Z = reshape_grid(x, y, z, n_list, d_list)
    
        #ax.plot_surface(xb, yb, zb, alpha=0.5, color="white")
        ax.plot_surface(X, Y, Z, cmap=cm.viridis)
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_zlabel("Average good info")
        ax.set_title(name)
        i += 1
    sync_viewing(axes, fig)


def plot_5_flat(datas, d_list, n_list, fig):
    #fig.suptitle("Average good info.", fontweight="bold")
    def map2goodinfo(data):
        N = []
        D = []
        I = []
        for d, n, runs in data:
            i = 0
            for run in runs:
                i += run.good_info
            if runs:
                i /= len(runs)
            N.append(n)
            D.append(d)
            I.append(i)
        return N, D, I
    gs = get_gridspec(datas)
    i = 0
    axes = []
    for name, data in datas:
        ax = fig.add_subplot(gs[i])
        axes.append(ax)
        x, y, z = map2goodinfo(data)
    
        n_list = list(range(500, 7100, 100))
        Z = np.empty((len(d_list), len(n_list)))
        for n, d, s in zip(x, y, z):
            if n < 8000:
                Z[d_list.index(d), n_list.index(n)] = s

        im = ax.imshow(Z, aspect="auto", interpolation="nearest", extent=(min(n_list), max(n_list), min(d_list), max(d_list)), origin="low")
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        #ax.set_zlabel("Average good info")
        ax.set_title(name)
        i += 1



def plot_6(datas, d_list, n_list, fig):
    fig.suptitle("Average bad info.", fontweight="bold")
    def map2badinfo(data):
        N = []
        D = []
        B = []
        for d, n, runs in data:
            b = 0
            for run in runs:
                b += run.bad_info
            b /= len(runs)
            N.append(n)
            D.append(d)
            B.append(b)
        return N, D, B
    gs = get_gridspec(datas)
    i = 0
    axes = []
    for name, data in datas:
        ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        x, y, z = map2badinfo(data)
        X, Y, Z = reshape_grid(x, y, z, n_list, d_list)
    
        ax.plot_surface(X, Y, Z, cmap=cm.viridis)
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_zlabel("Average bad info")
        ax.set_title(name)
        i += 1
    sync_viewing(axes, fig)


def plot_7(datas, d_list, n_list, fig):
    fig.suptitle("Average relative info.", fontweight="bold")
    def map2relativeinfo(data):
        N = []
        D = []
        R = []
        for d, n, runs in data:
            r = 0
            u = 0
            for run in runs:
                r += run.real_info
                u += run.info
            r /= u
            N.append(n)
            D.append(d)
            R.append(r)
        return N, D, R
    gs = get_gridspec(datas)
    i = 0
    axes = []
    for name, data in datas:
        ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        x, y, z = map2relativeinfo(data)
        X, Y, Z = reshape_grid(x, y, z, n_list, d_list)
        cmap = copy(cm.viridis)
        cmap.set_under("black")
        norm = Normalize(vmin=1)
    
        ax.plot_surface(X, Y, Z, cmap=cmap, norm=norm)
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_zlabel("Average relative info")
        ax.set_title(name)
        i += 1
    sync_viewing(axes, fig)


def plot_8(datas, d_list, n_list, fig):
    fig.suptitle("Average info.", fontweight="bold")
    def map2info(data):
        DS = {}
        for d, n, runs in data:
            s = DS.setdefault(d, 0)
            for run in runs:
                s += run.info
            s /= 5
            DS[d] = s
        return list(DS.keys()), list(DS.values())

    ax = fig.add_subplot(111)
    i = 0
    marks = "ox+ds^"
    for name, data in datas:
        x, y = map2info(data)
        ax.plot(x, y, label=name, marker=marks[i % len(marks)])
        i += 1
    ax.axhline(y=256, linestyle="dashed", alpha=0.8, label="256")
    ax.axhline(y=333, linestyle="dotted", alpha=0.8, label="256 * 1.3")
    ax.set_xlabel("Dimension of matrix (D)")
    ax.set_ylabel("Information in matrix")
    ax.legend()


def plot_9(datas, d_list, n_list, fig):
    fig.suptitle("Average bad info.", fontweight="bold")
    def map2info(data):
        DB = {}
        for d, n, runs in data:
            b = DB.setdefault(d, 0)
            for run in runs:
                b += run.bad_info
            b /= len(runs)
            DB[d] = b
        return list(DB.keys()), list(DB.values())

    ax = fig.add_subplot(111)
    i = 0
    marks = "ox+ds6^"
    for name, data in datas:
        bx, by = map2info(data)
        ax.plot(bx, by, marker=marks[i % len(marks)], label="Bad info ({})".format(name))
        i += 1
    ax.set_yscale("log")
    ax.set_xlabel("Dimension of matrix (D)")
    ax.set_ylabel("Average bad info (log-scale)")
    ax.legend()


def plot_10(datas, d_list, n_list, fig):
    #fig.suptitle("Success rate heatmaps.", fontweight="bold")
    def map2success(data):
        N = []
        D = []
        S = []
        min_n = None
        for d, n, runs in data:
            s = 0
            for run in runs:
                s += run.success
            if s != 0 and (min_n is None or min_n > n):
                min_n = n
            N.append(n)
            D.append(d)
            S.append(s)
        return N, D, S, min_n
    gs = get_gridspec(datas)
    #gs = gridspec.GridSpec(4, 1)
    i = 0
    axes = []
    for name, data in datas:
        ax = fig.add_subplot(gs[i])
        axes.append(ax)
        x, y, z, min_n = map2success(data)
        n_list = list(range(500, 7100, 100))
        Z = np.empty((len(d_list), len(n_list)))
        for n, d, s in zip(x, y, z):
            if n < 8000:
                Z[d_list.index(d), n_list.index(n)] = s
        #Z = np.empty((max(y)+1, max(x)+1))
        #for n, d, s in zip(x, y, z):
        #   Z[d, n] = s
        #a1 = [False for _ in range(max(y)+1)]
        #for l in d_list:
        #   a1[l] = True
        #a0 = [False for _ in range(max(x)+1)]
        #for l in n_list:
        #   if l <= 8000:
        #       a0[l] = True
        #Z = np.array(Z[:,a0])
        #Z = np.array(Z[a1,:])
        norm = Normalize(0, 5)
        
        im = ax.imshow(Z, norm=norm, aspect="auto", interpolation="nearest", extent=(min(n_list), max(n_list), min(d_list), max(d_list)), origin="low")
        if min_n is not None:
            ax.axvline(x=min_n, label="{}".format(min_n), color="red")
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_title(name.split("_")[0])
        i += 1
        ax.legend(loc="lower left")
    fig.subplots_adjust(top=0.965,bottom=0.065,left=0.110,right=0.845)
    #fig.subplots_adjust(right=0.8)
    #cbar_ax = fig.add_axes([0.90, 0.05, 0.05, 0.9])
    #fig.colorbar(im,cax=cbar_ax)


def plot_11(datas, d_list, n_list, fig):
    fig.suptitle("Average runtime in successful runs.", fontweight="bold")
    def map2runtime(data):
        N = []
        D = []
        T = []
        for d, n, runs in data:
            time = 0
            successes = 0
            for run in runs:
                if run.success:
                    time += run.time
                    successes += 1
            if successes != 0:
                t = time / successes
            else:
                t = 0
            N.append(n)
            D.append(d)
            T.append(t)
        return N, D, T
    gs = get_gridspec(datas)
    i = 0
    axes = []
    for name, data in datas:
        ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        x, y, z = map2runtime(data)
        X, Y, Z = reshape_grid(x, y, z, n_list, d_list)

        cmap = copy(cm.viridis)
        cmap.set_under("black")
        norm = Normalize(vmin=0.00001)
    
        ax.plot_surface(X, Y, Z, cmap=cmap, norm=norm)
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        ax.set_zlabel("Average runtime")
        ax.set_title(name)
        i += 1
    sync_viewing(axes, fig)

def plot_12_flat(datas, d_list, n_list, fig):
    #fig.suptitle("Average good info.", fontweight="bold")
    def map2info(data):
        N = []
        D = []
        I = []
        for d, n, runs in data:
            i = 0
            for run in runs:
                i += run.info
            if runs:
                i /= len(runs)
            N.append(n)
            D.append(d)
            I.append(i)
        return N, D, I
    gs = get_gridspec(datas)
    i = 0
    axes = []
    max_i = 0
    for name, data in datas:
        x, y, z = map2info(data)
        if max(z) > max_i:
            max_i = max(z)
    cmap = cm.get_cmap("viridis", max_i)
    for name, data in datas:
        ax = fig.add_subplot(gs[i])
        axes.append(ax)
        x, y, z = map2info(data)
    
        n_list = list(range(500, 7100, 100))
        Z = np.empty((len(d_list), len(n_list)))
        for n, d, s in zip(x, y, z):
            if n < 8000:
                Z[d_list.index(d), n_list.index(n)] = s

        im = ax.imshow(Z, aspect="auto", interpolation="nearest", cmap=cmap, extent=(min(n_list), max(n_list), min(d_list), max(d_list)), origin="low")
        ax.set_xlabel("Number of signatures (N)")
        ax.set_ylabel("Dimension of matrix (D)")
        #ax.set_zlabel("Average good info")
        ax.set_title(name)
        i += 1
    fig.subplots_adjust(right=0.8)
    cbar_ax = fig.add_axes([0.90, 0.05, 0.05, 0.9])
    #fig.colorbar(im, cax=cbar_ax)
    fig.colorbar(im, cax=cbar_ax)



desc = """\
Figures:
 - 1: Success rate, over dimension and number of sigs.
 - 2: Success rate, over number of sigs (summed through all dimensions).
 - 3: Average block size in successful runs, over dimension and number of sigs.
 - 4: Average number of liars, over dimension and number of sigs.
 - 5: Average good info, over dimension and number of sigs.
 - 6: Average bad info, over dimension and number of sigs.
 - 7: Average relative info(real/used), over dimension and number of sigs.
 - 8: Average info, over dimension (summed through all numbers of sigs).
"""

parser = argparse.ArgumentParser(description=desc)
parser.add_argument("--data", type=str, default="sim")
parser.add_argument("--figs", type=str, default="1,2,3,4,5,6,7,8,9,10,11,12")
parser.add_argument("bounds", type=str)

args = parser.parse_args()

d_list = list(range(50, 142, 2))
n_list = list(it.chain(range(500, 7100, 100), range(8000, 11000, 1000)))

runs = load_transformed("runs.pickle")

plt.style.use("fast")

figs = args.figs.split(",")
fs = [plot_1, plot_2_const, plot_3, plot_4_flat, plot_5_flat, plot_6, plot_7, plot_8, plot_9, plot_10, plot_11, plot_12_flat]
for i, f in enumerate(fs):
    if str(i+1) in figs:
        #fig = plt.figure(figsize=(7,8.2))
        #fig = plt.figure(figsize=(7,8.2*(2/3)))
        fig = plt.figure(figsize=(7,4))
        f(runs, d_list, n_list, fig)
        #fig.tight_layout()

plt.show()