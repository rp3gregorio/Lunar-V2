"""Unified plotting style for Phase 2 figures.

Design rules (per user request, 2026-05-10):
  * Legend never overlaps the data — always rendered in a separate box
    below the axes, with bbox_to_anchor and a thin border.
  * Sans-serif typography, 11 pt body / 10 pt legend / 12 pt title.
  * One palette across the whole replication: red = Hayne, blue = M&S,
    grey = observational reference (Diviner / Apollo / daveTemp).
  * 0.3 alpha grid, no top/right spines.

Use these via::

    from lunar.phase2_plotting import (
        apply_phase2_style, legend_below, COLORS, savefig_pair,
    )

Call ``apply_phase2_style()`` once at the top of any Phase 2 script /
notebook cell to set rcParams, then ``legend_below(ax, ...)`` instead of
``ax.legend(...)`` to keep legends out of the data area.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Phase 2 colour palette
# ---------------------------------------------------------------------------
COLORS = {
    "hayne": "#d62728",       # red
    "ms": "#1f77b4",          # blue (Martinez & Siegler)
    "vasavada": "#ff7f0e",    # orange
    "woods_robinson": "#2ca02c",  # green
    "diviner": "#333333",     # dark grey for observations
    "apollo": "#9467bd",      # purple
    "highlight": "#e377c2",   # pink — for callouts (e.g. 4-m line)
    "shade": "0.85",          # neutral shading
}


def apply_phase2_style() -> None:
    """Apply the Phase 2 rcParams. Idempotent — safe to call repeatedly."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 11.0,
        "axes.titlesize": 12.0,
        "axes.labelsize": 11.0,
        "xtick.labelsize": 10.0,
        "ytick.labelsize": 10.0,
        "legend.fontsize": 10.0,
        "legend.framealpha": 1.0,
        "legend.edgecolor": "0.6",
        "legend.fancybox": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.5,
        "savefig.bbox": "tight",
        "savefig.dpi": 150,
        "figure.constrained_layout.use": False,  # we manage layout manually
    })


def legend_below(
    ax: plt.Axes,
    *,
    ncol: int | None = None,
    pad: float = 0.18,
    box_relative_height: float = 0.13,
    fontsize: float | None = None,
    title: str | None = None,
) -> mpl.legend.Legend:
    """Render the axes legend in a box BELOW the data area.

    The legend is anchored to the bottom of the figure (not the axes),
    so it never overlaps the plotted data regardless of axis range.

    Parameters
    ----------
    ax : the axes whose handles/labels to use.
    ncol : columns in the legend. Default: split entries evenly across
        rows so width <= 4 entries per row.
    pad : space (figure-relative units) between the axes bottom and the
        top of the legend box. 0.18 works for most single-row legends;
        increase to ~0.22 for two-row legends.
    box_relative_height : approximate vertical extent of the legend box
        in figure-relative units (used to leave room when calling
        fig.subplots_adjust).
    fontsize : override rcParams legend.fontsize.
    title : optional legend title.

    Returns
    -------
    The matplotlib Legend object (so callers can further tweak).

    Notes
    -----
    Calls ``ax.figure.subplots_adjust(bottom=...)`` to make room — be
    sure to call this *after* the data has been plotted but *before*
    saving the figure. Do not also pass ``constrained_layout=True`` to
    plt.subplots; that fights with the manual subplots_adjust here.
    """
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        raise ValueError("No legend handles on this axes — plot data first.")

    if ncol is None:
        ncol = min(4, len(handles))
    n_rows = (len(handles) + ncol - 1) // ncol

    fig = ax.figure
    bottom_pad = pad + 0.04 * max(0, n_rows - 1)
    fig.subplots_adjust(bottom=bottom_pad + 0.10)

    leg = fig.legend(
        handles, labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        ncol=ncol,
        fontsize=fontsize if fontsize is not None else mpl.rcParams["legend.fontsize"],
        frameon=True,
        framealpha=1.0,
        edgecolor="0.6",
        title=title,
        title_fontsize=mpl.rcParams["legend.fontsize"],
    )
    return leg


def savefig_pair(fig: plt.Figure, base_path: Path | str, dpi: int = 150) -> None:
    """Save the figure as both PDF and PNG with the same base path."""
    base = Path(base_path).with_suffix("")
    fig.savefig(base.with_suffix(".pdf"))
    fig.savefig(base.with_suffix(".png"), dpi=dpi)


def shoemaker_target() -> dict:
    """Constants for the Shoemaker tile used throughout Phase 2."""
    return {"lat": -87.9102, "lon": 45.5073, "name": "Shoemaker PSR"}
