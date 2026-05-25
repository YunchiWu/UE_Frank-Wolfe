"""Convergence indicators for the Frank-Wolfe iterations."""

from __future__ import annotations

import numpy as np

def flow_change_norm(x_new: np.ndarray, x_old: np.ndarray) -> float:
    """Equation [5.8b]: sqrt(sum (Δx)^2) / sum(x)."""
    denom = float(np.sum(x_old))
    if denom <= 0.0:
        return float("inf")
    return float(np.linalg.norm(x_new - x_old)) / denom


def relative_gap(link_flows: np.ndarray, link_times: np.ndarray, sptt: float) -> float:
    """Relative gap: (TSTT - SPTT) / TSTT."""
    tstt = float(np.dot(link_flows, link_times))
    if tstt <= 0.0 or not np.isfinite(sptt):
        return float("inf")
    return (tstt - float(sptt)) / tstt
