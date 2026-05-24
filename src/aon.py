"""All-or-Nothing network loading."""

from __future__ import annotations

import numpy as np

from .network import Network
from .shortest_path import shortest_path_tree


def all_or_nothing(
    network: Network,
    travel_times: np.ndarray,
    demand: np.ndarray,
) -> tuple[np.ndarray, float]:
    """Load OD demand onto shortest paths and return link flows.

    Returns:
        link_flows: array of shape (n_links,)
        sptt: shortest-path total travel time, sum_{rs} q_{rs} * u_{rs}.
              Useful for the relative gap.
    """
    n_links = network.n_links
    n_zones = network.n_zones
    flows = np.zeros(n_links, dtype=np.float64)
    sptt = 0.0

    tail = network.tail

    for r in range(n_zones):
        row = demand[r]
        if not np.any(row > 0.0):
            continue
        labels, pred_link = shortest_path_tree(network, travel_times, r)
        for s in range(n_zones):
            q = row[s]
            if q <= 0.0 or s == r:
                continue
            u_rs = labels[s]
            if not np.isfinite(u_rs):
                continue
            sptt += q * u_rs
            node = s
            while node != r:
                k = int(pred_link[node])
                if k < 0:
                    break
                flows[k] += q
                node = int(tail[k])

    return flows, sptt