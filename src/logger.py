"""Lightweight iteration logger."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IterRecord:
    n: int
    objective: float
    gap: float
    alpha: float


@dataclass
class IterationLog:
    records: list[IterRecord] = field(default_factory=list)
    verbose: bool = True

    def log(self, n: int, objective: float, gap: float, alpha: float) -> None:
        self.records.append(IterRecord(n, objective, gap, alpha))
        if self.verbose:
            print(
                f"iter {n:4d}  z = {objective:.6e}  "
                f"gap = {gap:.3e}  alpha = {alpha:.4f}"
            )