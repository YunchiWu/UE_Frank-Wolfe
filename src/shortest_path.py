"""Moore-Pape label-correcting shortest-path algorithm.

Implements the deque-based sequence-list strategy described in Sheffi
(1985), Section 5.3: nodes never seen before are appended to the tail;
previously examined nodes that need re-examination are prepended to
the head.
"""

from __future__ import annotations

from collections import deque
import numpy as np

from .network import Network


_IN_LIST = 1
_REMOVED = 2


def shortest_path_tree(
    network: Network,
    travel_times: np.ndarray,
    origin: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (labels, predecessor_link) for shortest paths from `origin`.

    `predecessor_link[j]` is the index of the link that enters node j on
    the shortest path tree (-1 for the origin and unreachable nodes).

    Nodes with index < ``network.first_thru_node`` are treated as zones
    (centroids) and are only permitted as the origin or a destination —
    their outgoing links are not relaxed when they would be used as a
    transit node. This matches the TNTP ``<FIRST THRU NODE>`` convention.
    """
    n = network.n_nodes
    INF = np.inf

    labels = np.full(n, INF, dtype=np.float64)
    pred_link = np.full(n, -1, dtype=np.int64)
    status = np.zeros(n, dtype=np.int8)

    labels[origin] = 0.0
    dq: deque[int] = deque()
    dq.append(origin)
    status[origin] = _IN_LIST

    B = network.B
    head = network.head
    first_thru = network.first_thru_node

    while dq:
        i = dq.popleft()
        status[i] = _REMOVED
        # Skip transit through non-thru zones (origin is always allowed).
        if i != origin and i < first_thru:
            continue
        li = labels[i]
        for k in range(int(B[i]), int(B[i + 1])):
            j = int(head[k])
            new_label = li + travel_times[k]
            if new_label < labels[j]:
                labels[j] = new_label
                pred_link[j] = k
                if status[j] == _IN_LIST:
                    continue
                if status[j] == _REMOVED:
                    dq.appendleft(j)
                else:
                    dq.append(j)
                status[j] = _IN_LIST

    return labels, pred_link