"""Network data structure in forward-star form."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class Network:
    """Forward-star representation of a directed road network.

    Node indices are 0-based internally. Links are sorted by tail node so
    that all links emanating from the same node occupy a contiguous slice
    of the link arrays.

    Attributes:
        n_nodes: number of nodes.
        n_links: number of directed links.
        n_zones: number of OD zones (zones are assumed to be the first
            `n_zones` nodes).
        first_thru_node: 0-based index of the first node that is allowed
            to be used as a pass-through (transit) node. Nodes with index
            strictly smaller than this are zones (centroids) that may
            serve only as the origin or destination of a trip, never as
            an intermediate. When the TNTP file sets ``<FIRST THRU NODE>``
            to 1, this is 0 and every node is a thru node.
        tail: int array of shape (n_links,), tail node of each link.
        head: int array of shape (n_links,), head node of each link.
        B: int array of shape (n_nodes + 1,), forward-star pointer.
            Links emanating from node i are link indices in [B[i], B[i+1]).
        fft: free-flow travel time per link.
        cap: capacity per link.
        alpha, beta: BPR parameters per link.
    """

    n_nodes: int
    n_links: int
    n_zones: int
    first_thru_node: int
    tail: np.ndarray
    head: np.ndarray
    B: np.ndarray
    fft: np.ndarray
    cap: np.ndarray
    alpha: np.ndarray
    beta: np.ndarray

    def outgoing(self, i: int) -> range:
        """Return the link index range emanating from node `i` (0-based)."""
        return range(int(self.B[i]), int(self.B[i + 1]))


def build_network(
    tail: np.ndarray,
    head: np.ndarray,
    fft: np.ndarray,
    cap: np.ndarray,
    alpha: np.ndarray,
    beta: np.ndarray,
    n_nodes: int,
    n_zones: int,
    first_thru_node: int = 0,
) -> Network:
    """Sort links by tail and construct the forward-star pointer array.

    Inputs use 0-based node indices.
    """
    tail = np.asarray(tail, dtype=np.int64)
    head = np.asarray(head, dtype=np.int64)
    fft = np.asarray(fft, dtype=np.float64)
    cap = np.asarray(cap, dtype=np.float64)
    alpha = np.asarray(alpha, dtype=np.float64)
    beta = np.asarray(beta, dtype=np.float64)

    order = np.argsort(tail, kind="stable")
    tail = tail[order]
    head = head[order]
    fft = fft[order]
    cap = cap[order]
    alpha = alpha[order]
    beta = beta[order]

    n_links = tail.shape[0]
    B = np.zeros(n_nodes + 1, dtype=np.int64)
    counts = np.bincount(tail, minlength=n_nodes)
    B[1:] = np.cumsum(counts)

    return Network(
        n_nodes=n_nodes,
        n_links=n_links,
        n_zones=n_zones,
        first_thru_node=int(first_thru_node),
        tail=tail,
        head=head,
        B=B,
        fft=fft,
        cap=cap,
        alpha=alpha,
        beta=beta,
    )
