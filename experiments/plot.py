from copy import copy
from math import sqrt, ceil
import itertools as it


import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm, gridspec
from matplotlib.colors import Normalize
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter)


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


def plot_todim(datas, fig, map_func, ylabel):
    ax = fig.add_subplot(111)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Dimension of matrix (D)")
    for name, data in sorted(datas.items()):
        value = map_func(data["runs"])
        ax.plot(d_list, value, label=data["name"])
    ax.legend()
    return ax


def plot_toN(datas, fig, map_func, ylabel, map_color=True, map_lines=True):
    ax = fig.add_subplot(111)
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(MultipleLocator(1000))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(MultipleLocator(100))
    ax.set_xlabel("Number of signatures (N)")
    lines = ["-", "--", "-.", ":"]
    ls = []
    cm = plt.get_cmap("tab20c")
    cs = []
    for name, data in sorted(datas.items()):
        value = map_func(data["runs"])
        if name[-1] not in ls:
            ls.append(name[-1])
        if name[0] not in cs:
            cs.append(name[0])
        color = cm((cs.index(name[0]) * 4)/20)
        ax.plot(n_list, value, label=data["name"], linestyle=lines[ls.index(name[-1])] if map_lines else "-", color=color if map_color else None)
    ax.legend()
    return ax    

def plot_dim(datas, fig, map_func, dim, ylabel, map_color=True, map_lines=True):
    ax = fig.add_subplot(111)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Index")
    lines = ["-", "--", "-.", ":"]
    ls = []
    cm = plt.get_cmap("tab20c")
    cs = []
    for name, data in sorted(datas.items()):
        value = map_func(data["runs"], dim)
        if name[-1] not in ls:
            ls.append(name[-1])
        if name[0] not in cs:
            cs.append(name[0])
        color = cm((cs.index(name[0]) * 4)/20)
        ax.plot(range(dim), value, label=data["name"], linestyle=lines[cs.index(name[0])] if map_lines else "-", color=color if map_color else None)
    ax.legend()
    return ax

def plot_heatmap(datas, fig, map_func, zlabel, flat=True, grid=None, ns=n_list, ds=d_list, xlabel="Number of signatures (N)", ylabel="Dimension of matrix (D)", vmin=None, vmax=None):
    gs = get_gridspec(datas, grid)
    i = 0
    axes = []
    for name, data in sorted(datas.items()):
        ax_xlabel = ""
        ax_ylabel = ""
        rc = gs[i].get_rows_columns()
        if rc[2] == rc[0] - 1:
            ax_xlabel = xlabel
        if rc[4] == 0:
            ax_ylabel = ylabel
        if flat:
            ax = fig.add_subplot(gs[i])
        else:
            ax = fig.add_subplot(gs[i], projection="3d")
        axes.append(ax)
        print("mapping", name, data["name"])
        x, y, z, min_n = map_func(data["runs"])
        X, Y, Z = reshape_grid(x, y, z, ns, ds)
        cmap = copy(cm.get_cmap("viridis"))
        cmap.set_under((1,1,1,1.0))
        #cmap.set_under((0.77,0.77,0.77))
        #norm = Normalize(vmin=-0.0001)
        norm = None
        if flat:
            im = ax.pcolormesh(X, Y, Z, cmap=cmap, norm=norm, vmin=vmin, vmax=vmax, rasterized=True)
            if min_n is not None:
                ax.axvline(x=min_n, label="{}".format(min_n), color="red", linestyle="--", alpha=0.7)
            
        else:
            ax.plot_surface(X, Y, Z, cmap=cmap, norm=norm)
            ax.set_zlabel(zlabel)
        ax.set_xlabel(ax_xlabel)
        ax.set_ylabel(ax_ylabel)
        if ns == n_list:
            ax.set_xticks([500,2000,4000,6000,8000,10000])
        ax.set_title(data["name"])
        i += 1
    if flat:
        if len(axes) == 1 or len(axes) == 2:
            cbar_ax = fig.add_axes((0.93, 0.183, 0.02, 0.70))
        else:
            cbar_ax = fig.add_axes((0.93, 0.079, 0.02, 0.87))
        fig.colorbar(im, cax=cbar_ax)
    else:
        sync_viewing(axes, fig)
    return axes
