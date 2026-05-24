"""Frank-Wolfe (convex combinations) algorithm for the static UE problem."""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from .network import Network
from .bpr import travel_time, integral
from .aon import all_or_nothing
from .line_search import bisection
from .convergence import flow_change_norm
from .logger import IterationLog


@dataclass
class FWOptions:
    max_iter: int = 100
    gap_tol: float = 1e-4
    ls_tol: float = 1e-6
    ls_max_iter: int = 50
    verbose: bool = True


@dataclass
class FWResult:
    link_flows: np.ndarray
    link_times: np.ndarray
    n_iter: int
    final_gap: float
    objective: float
    log: IterationLog = field(default_factory=IterationLog)


def frank_wolfe(
    network: Network,
    demand: np.ndarray,
    options: FWOptions | None = None,
) -> FWResult:
    """Solve the user-equilibrium problem via the Frank-Wolfe method."""
    if options is None:
        options = FWOptions()

    log = IterationLog(verbose=options.verbose)

    # Step 0: empty-network AON.
    t = travel_time(np.zeros(network.n_links), network)
    x, _ = all_or_nothing(network, t, demand)

    gap = float("inf")
    n = 0
    for n in range(1, options.max_iter + 1):
        # Step 1: update link times.
        t = travel_time(x, network)
        # Step 2: direction finding via AON on current times.
        y, _ = all_or_nothing(network, t, demand)
        # Step 3: line search.
        alpha = bisection(x, y, network, tol=options.ls_tol, max_iter=options.ls_max_iter)
        # Step 4: move.
        x_new = x + alpha * (y - x)
        # Convergence check based on equation [5.8b].
        gap = flow_change_norm(x_new, x)

        z = integral(x_new, network)
        log.log(n, z, gap, alpha)

        x = x_new
        if gap < options.gap_tol:
            break

    t = travel_time(x, network)
    return FWResult(
        link_flows=x,
        link_times=t,
        n_iter=n,
        final_gap=gap,
        objective=integral(x, network),
        log=log,
    )
