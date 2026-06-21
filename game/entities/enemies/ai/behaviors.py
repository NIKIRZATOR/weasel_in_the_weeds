from __future__ import annotations

import math
import random

from game.core.vector import Vector2


def can_detect_player(enemy, player, distance_to_player):
    if distance_to_player > enemy.detection_radius:
        return False
    if not getattr(player, "is_hidden", False):
        return True
    return distance_to_player <= enemy.HIDDEN_REVEAL_RADIUS


def start_chase(enemy, player_center):
    direction = Vector2(player_center.x - enemy.get_center().x, player_center.y - enemy.get_center().y)
    if direction.length() > 0:
        enemy.last_chase_direction = direction.normalize()
    enemy.behavior_state = "chase"
    enemy.linger_timer = enemy.linger_duration
    enemy.path_recalc_timer = 0.0


def pick_patrol_target(enemy):
    center = enemy._home_center()
    angle = random.uniform(0, math.tau)
    radius = random.uniform(enemy.width * 0.5, enemy.patrol_radius)
    return Vector2(
        center.x + math.cos(angle) * radius,
        center.y + math.sin(angle) * radius,
    )

