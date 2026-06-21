from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnemyAttackProfile:
    damage: int = 1
    range: float = 40.0
    windup: float = 0.0
    recovery: float = 0.0
    cooldown: float = 1.0
