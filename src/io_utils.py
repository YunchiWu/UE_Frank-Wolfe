"""Readers for TNTP network and trip files."""

from __future__ import annotations

import re
from pathlib import Path
import numpy as np

from .network import Network, build_network


def _read_metadata(lines):
    meta = {}
    end_idx = 0
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("<END OF METADATA>"):
            end_idx = idx + 1
            break
        m = re.match(r"<([^>]+)>\s*(.*)", s)
        if m:
            meta[m.group(1).strip().upper()] = m.group(2).strip()
    return meta, end_idx


def load_network(net_file: str | Path) -> Network:
    """Parse a TNTP `_net.tntp` file and return a :class:`Network`.

    Node indices in the file are 1-based; internally we store them 0-based.
    """
    path = Path(net_file)
    lines = path.read_text().splitlines()
    meta, body_start = _read_metadata(lines)

    n_nodes = int(meta["NUMBER OF NODES"])
    n_zones = int(meta["NUMBER OF ZONES"])
    n_links = int(meta["NUMBER OF LINKS"])
    # FIRST THRU NODE is 1-based in the file; convert to 0-based.
    # Default to 1 → 0, meaning every node may transit.
    first_thru_node_raw = int(meta.get("FIRST THRU NODE", "1"))
    first_thru_node = max(0, first_thru_node_raw - 1)

    tails, heads, fft, cap, alpha, beta = [], [], [], [], [], []
    for raw in lines[body_start:]:
        s = raw.strip()
        if not s or s.startswith("~") or s.startswith("<"):
            continue
        s = s.rstrip(";").strip()
        parts = s.split()
        if len(parts) < 7:
            continue
        try:
            t = int(parts[0])
            h = int(parts[1])
        except ValueError:
            continue
        # Columns: tail head capacity length fft b power speed toll type
        tails.append(t - 1)
        heads.append(h - 1)
        cap.append(float(parts[2]))
        # parts[3] is length, skip
        fft.append(float(parts[4]))
        alpha.append(float(parts[5]))
        beta.append(float(parts[6]))

    if len(tails) != n_links:
        # Some TNTP files have minor mismatches; trust the parsed rows.
        n_links = len(tails)

    return build_network(
        tail=np.array(tails),
        head=np.array(heads),
        fft=np.array(fft),
        cap=np.array(cap),
        alpha=np.array(alpha),
        beta=np.array(beta),
        n_nodes=n_nodes,
        n_zones=n_zones,
        first_thru_node=first_thru_node,
    )


def load_flow_reference(
    flow_file: str | Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Parse a TNTP ``_flow.tntp`` file.

    Returns three parallel arrays (tail, head, volume) with 0-based node
    indices. The fourth column (cost / link travel time at equilibrium)
    is also returned for convenience.

    The first line is always ``From\tTo\tVolume\tCost``.
    """
    path = Path(flow_file)
    tails, heads, vols, costs = [], [], [], []
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s:
            continue
        parts = s.split()
        # Skip the header row by checking whether the first token is numeric.
        try:
            t = int(parts[0])
            h = int(parts[1])
        except (ValueError, IndexError):
            continue
        tails.append(t - 1)
        heads.append(h - 1)
        vols.append(float(parts[2]))
        costs.append(float(parts[3]) if len(parts) > 3 else 0.0)
    return (
        np.array(tails, dtype=np.int64),
        np.array(heads, dtype=np.int64),
        np.array(vols, dtype=np.float64),
        np.array(costs, dtype=np.float64),
    )


def load_demand(trips_file: str | Path, n_zones: int | None = None) -> np.ndarray:
    """Parse a TNTP `_trips.tntp` file and return a dense OD matrix.

    Returns an array of shape (n_zones, n_zones), 0-based indexing.
    """
    path = Path(trips_file)
    text = path.read_text()
    lines = text.splitlines()
    meta, body_start = _read_metadata(lines)
    if n_zones is None:
        n_zones = int(meta["NUMBER OF ZONES"])

    od = np.zeros((n_zones, n_zones), dtype=np.float64)

    current_origin = None
    entry_re = re.compile(r"(\d+)\s*:\s*([0-9eE\.\+\-]+)")
    origin_re = re.compile(r"Origin\s+(\d+)", re.IGNORECASE)

    for raw in lines[body_start:]:
        s = raw.strip()
        if not s:
            continue
        m = origin_re.match(s)
        if m:
            current_origin = int(m.group(1)) - 1
            continue
        if current_origin is None:
            continue
        for dest_str, flow_str in entry_re.findall(s):
            d = int(dest_str) - 1
            q = float(flow_str)
            if 0 <= d < n_zones and 0 <= current_origin < n_zones:
                od[current_origin, d] = q

    return od