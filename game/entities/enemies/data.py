from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnemyDefinition:
    id: str
    max_health: int
    speed: int
    damage: int
    xp_reward: int = 10
    detection_radius: int = 160
