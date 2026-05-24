"""Bisection (Bolzano) line search for the Frank-Wolfe step size."""

from __future__ import annotations

import numpy as np

from .network import Network
from .bpr import travel_time


def _phi_prime(alpha: float, x: np.ndarray, d: np.ndarray, network: Network) -> float:
    """Directional derivative of the Beckmann objective along d at step alpha."""
    flows = x + alpha * d
    np.maximum(flows, 0.0, out=flows)
    t = travel_time(flows, network)
    return float(np.dot(d, t))


def bisection(
    x: np.ndarray,
    y: np.ndarray,
    network: Network,
    tol: float = 1e-5,
    max_iter: int = 50,
) -> float:
    """Find alpha in [0, 1] minimising z(x + alpha (y - x))."""
    d = y - x

    g0 = _phi_prime(0.0, x, d, network)
    if g0 >= 0.0:
        return 0.0
    g1 = _phi_prime(1.0, x, d, network)
    if g1 <= 0.0:
        return 1.0

    lo, hi = 0.0, 1.0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        g = _phi_prime(mid, x, d, network)
        if g > 0.0:
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)