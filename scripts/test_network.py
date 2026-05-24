"""Run the Frank-Wolfe solver test for one configured network.

Change :data:`NETWORK_NAME` to switch networks, for example from
``"SiouxFalls"`` to ``"Winnipeg"``.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

# Change this value to test a different configured network.
NETWORK_NAME = "Winnipeg"
NET_FILE = f"{NETWORK_NAME}_net.tntp"
TRIPS_FILE = f"{NETWORK_NAME}_trips.tntp"
FLOW_FILE = f"{NETWORK_NAME}_flow.tntp"
MAX_ITER = 3000
GAP_TOL = 1e-5

# Make `src` importable regardless of where this script is launched from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np  # noqa: E402

from src import (  # noqa: E402
    FWOptions,
    frank_wolfe,
    load_demand,
    load_flow_reference,
    load_network,
)

DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"


def _resolve_paths() -> tuple[Path, Path, Path | None]:
    base = DATA_DIR / NETWORK_NAME
    net_path = base / NET_FILE
    trips_path = base / TRIPS_FILE
    if not net_path.exists():
        raise FileNotFoundError(f"net file not found: {net_path}")
    if not trips_path.exists():
        raise FileNotFoundError(f"trips file not found: {trips_path}")

    flow_path: Path | None = None
    if FLOW_FILE:
        candidate = base / FLOW_FILE
        if candidate.exists():
            flow_path = candidate
    return net_path, trips_path, flow_path


def _ensure_results_dir(name: str) -> Path:
    out = RESULTS_DIR / name
    out.mkdir(parents=True, exist_ok=True)
    return out


def _compare_flows(network, link_flows: np.ndarray, flow_file: Path) -> dict:
    t_ref, h_ref, vol_ref, _ = load_flow_reference(flow_file)
    lookup = {
        (int(t), int(h)): float(v)
        for t, h, v in zip(network.tail, network.head, link_flows)
    }
    matched = np.array(
        [lookup.get((int(t), int(h)), 0.0) for t, h in zip(t_ref, h_ref)],
        dtype=np.float64,
    )
    diff = matched - vol_ref
    denom = np.linalg.norm(vol_ref) + 1e-12
    l2_rel = float(np.linalg.norm(diff) / denom)
    with np.errstate(divide="ignore", invalid="ignore"):
        per_link_rel = np.where(vol_ref > 1e-9, np.abs(diff) / vol_ref, 0.0)
    return {
        "l2_rel": l2_rel,
        "max_rel": float(per_link_rel.max()) if per_link_rel.size else 0.0,
        "n_over": int(np.sum(diff > 0.0)),
        "n_under": int(np.sum(diff < 0.0)),
        "n_compared": int(vol_ref.size),
    }


def _save_link_flows(network, flows: np.ndarray, times: np.ndarray, path: Path) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tail", "head", "volume", "travel_time"])
        for t, h, v, c in zip(network.tail, network.head, flows, times):
            w.writerow([int(t) + 1, int(h) + 1, f"{float(v):.6f}", f"{float(c):.6f}"])


def _save_convergence_log(log, path: Path) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iter", "objective", "gap", "alpha"])
        for r in log.records:
            w.writerow([r.n, f"{r.objective:.6e}", f"{r.gap:.6e}", f"{r.alpha:.6f}"])


def run_network_test() -> dict:
    """Run the end-to-end Frank-Wolfe test for the configured network."""
    net_path, trips_path, flow_path = _resolve_paths()

    print(f"=== Frank-Wolfe UE Solver: {NETWORK_NAME} ===")

    network = load_network(net_path)
    demand = load_demand(trips_path, n_zones=network.n_zones)

    print(
        f"Network:  n_nodes={network.n_nodes}  n_links={network.n_links}  "
        f"n_zones={network.n_zones}  first_thru_node={network.first_thru_node}"
    )
    print(f"Demand :  total = {float(demand.sum()):.1f}")
    print(f"Solver :  max_iter={MAX_ITER}  gap_tol={GAP_TOL:.1e}")

    options = FWOptions(
        max_iter=MAX_ITER,
        gap_tol=GAP_TOL,
        verbose=False,
    )
    t0 = time.time()
    result = frank_wolfe(network, demand, options)
    elapsed = time.time() - t0

    print(
        f"Result :  iters={result.n_iter}  final_gap={result.final_gap:.3e}  "
        f"objective={result.objective:.4e}  elapsed={elapsed:.2f}s"
    )

    cmp_metrics: dict = {}
    if flow_path is not None:
        cmp_metrics = _compare_flows(network, result.link_flows, flow_path)
        print(
            f"Compare:  flow L2 rel err = {cmp_metrics['l2_rel']:.3e}  "
            f"max single-link rel err = {cmp_metrics['max_rel']:.3e}  "
            f"(n_links_compared = {cmp_metrics['n_compared']})"
        )
    else:
        print("Compare:  no reference flow file, skipping comparison")

    out_dir = _ensure_results_dir(NETWORK_NAME)
    flows_csv = out_dir / "link_flows.csv"
    log_csv = out_dir / "convergence_log.csv"
    _save_link_flows(network, result.link_flows, result.link_times, flows_csv)
    _save_convergence_log(result.log, log_csv)
    print(f"Output :  {flows_csv}")
    print(f"          {log_csv}")

    print("[DONE]")

    return {
        "name": NETWORK_NAME,
        "n_iter": result.n_iter,
        "final_gap": result.final_gap,
        "objective": result.objective,
        "elapsed_s": elapsed,
        **cmp_metrics,
    }


def main() -> None:
    run_network_test()


if __name__ == "__main__":
    main()
