"""Plot Frank-Wolfe convergence curves for a single network.

Change :data:`NETWORK_NAME` to switch networks, for example from
``"SiouxFalls"`` to ``"Winnipeg"``.

Usage:
    python scripts/plot_convergence.py

Reads ``results/<NetworkName>/convergence_log.csv`` and writes:

* ``results/<NetworkName>/gap_vs_iter.png``       — relative gap (log y-axis)
* ``results/<NetworkName>/objective_vs_iter.png`` — Beckmann objective z(x)
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

# Change this value to plot a different network's convergence curves.
NETWORK_NAME = "Winnipeg"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"


def _load_log(path: Path) -> tuple[list[int], list[float], list[float]]:
    iters: list[int] = []
    objs: list[float] = []
    gaps: list[float] = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            iters.append(int(row["iter"]))
            objs.append(float(row["objective"]))
            gaps.append(float(row["gap"]))
    return iters, objs, gaps


def plot_convergence(name: str, results_dir: Path = RESULTS_DIR) -> None:
    net_dir = results_dir / name
    log_path = net_dir / "convergence_log.csv"
    if not log_path.exists():
        print(f"Convergence log not found: {log_path}")
        sys.exit(1)

    iters, objs, gaps = _load_log(log_path)
    if not iters:
        print(f"Empty convergence log: {log_path}")
        sys.exit(1)

    gx = [i for i, g in zip(iters, gaps) if g > 0.0]
    gy = [g for g in gaps if g > 0.0]

    fig_gap, ax_gap = plt.subplots(figsize=(8, 5))
    ax_gap.plot(gx, gy, marker=".", linewidth=1.2, color="C0")
    ax_gap.set_yscale("log")
    ax_gap.set_xlabel("Iteration")
    ax_gap.set_ylabel("Relative gap (log scale)")
    ax_gap.set_title(f"Frank-Wolfe convergence: gap vs iteration ({name})")
    ax_gap.grid(True, which="both", linestyle=":", alpha=0.5)

    fig_obj, ax_obj = plt.subplots(figsize=(8, 5))
    ax_obj.plot(iters, objs, marker=".", linewidth=1.2, color="C1")
    ax_obj.set_xlabel("Iteration")
    ax_obj.set_ylabel("Objective z(x)")
    ax_obj.set_title(f"Frank-Wolfe convergence: objective vs iteration ({name})")
    ax_obj.grid(True, linestyle=":", alpha=0.5)

    gap_path = net_dir / "gap_vs_iter.png"
    obj_path = net_dir / "objective_vs_iter.png"
    fig_gap.tight_layout()
    fig_obj.tight_layout()
    fig_gap.savefig(gap_path, dpi=150)
    fig_obj.savefig(obj_path, dpi=150)

    print(
        f"{name:15s} iters={iters[-1]:5d}  "
        f"final_gap={gaps[-1]:.3e}  final_obj={objs[-1]:.4e}"
    )
    print(f"Saved {gap_path}")
    print(f"Saved {obj_path}")


def main() -> None:
    plot_convergence(NETWORK_NAME)


if __name__ == "__main__":
    main()
