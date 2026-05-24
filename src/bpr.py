"""BPR link performance function and its definite integral."""

from __future__ import annotations

import numpy as np

from .network import Network


def travel_time(x: np.ndarray, network: Network) -> np.ndarray:
    """Vectorised BPR: t = fft * (1 + alpha * (x/cap)**beta)."""
    ratio = x / network.cap
    return network.fft * (1.0 + network.alpha * np.power(ratio, network.beta))


def integral(x: np.ndarray, network: Network) -> float:
    """Beckmann objective: \sum_a \int_0^{x_a} t_a(\omega) d\omega.

    For BPR with exponent beta:
        \int_0^x fft (1 + alpha (\omega/cap)**\beta) d\omega
        = fft * x + fft * alpha * cap / (\beta+1) * (x/cap)**(\beta+1)
    """
    ratio = x / network.cap
    term1 = network.fft * x
    term2 = network.fft * network.alpha * network.cap / (network.beta + 1.0) \
        * np.power(ratio, network.beta + 1.0)
    return float(np.sum(term1 + term2))