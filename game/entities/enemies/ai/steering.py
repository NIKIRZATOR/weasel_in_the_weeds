from __future__ import annotations

import math


def rects_intersect(rect_a, rect_b):
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def point_distance(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy)


def rect_distance(rect_a, rect_b):
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b
    dx = max(bx - (ax + aw), ax - (bx + bw), 0)
    dy = max(by - (ay + ah), ay - (by + bh), 0)
    return math.sqrt(dx * dx + dy * dy)


def entity_distance(entity_a, entity_b):
    circle_a = entity_a.get_collision_circle() if getattr(entity_a, "has_collision_circle", lambda: False)() else None
    circle_b = entity_b.get_collision_circle() if getattr(entity_b, "has_collision_circle", lambda: False)() else None
    if circle_a is not None and circle_b is not None:
        ax, ay, ar = circle_a
        bx, by, br = circle_b
        center_distance = math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
        return max(0.0, center_distance - ar - br)

    return rect_distance(entity_a.get_hitbox_rect(), entity_b.get_hitbox_rect())

