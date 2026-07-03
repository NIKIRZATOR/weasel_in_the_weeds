import math
from types import SimpleNamespace

import pygame

from game.core.assets import load_image
from game.core.vector import Vector2
from game.entities.enemies.ai.steering import rects_intersect
from settings import ASSETS_DIR, COLORS


_ARROW_SPRITE: pygame.Surface | None = None


def _get_arrow_sprite(size: tuple[int, int]) -> pygame.Surface | None:
    global _ARROW_SPRITE
    if _ARROW_SPRITE is None:
        _ARROW_SPRITE = load_image(ASSETS_DIR / "items" / "weapons" / "arrow.png", size=size)
    return _ARROW_SPRITE


class PlayerProjectile:
    def __init__(self, x, y, dir_x, dir_y, speed, damage, radius=5, max_distance=520.0, sprite_scale=1.0):
        self.position = Vector2(x, y)
        direction = Vector2(dir_x, dir_y)
        self.direction = direction.normalize() if direction.length() > 0 else Vector2(1, 0)
        self.speed = float(speed)
        self.damage = max(1, int(damage))
        self.radius = max(2, int(radius))
        self.max_distance = float(max_distance)
        self.sprite_scale = max(0.5, float(sprite_scale))
        self.travelled_distance = 0.0
        self.is_dead = False
        self.collision_probe = _ProjectileProbe(self.radius)
        sprite_size = (
            max(int(self.radius * 8 * self.sprite_scale), 16),
            max(int(self.radius * 3 * self.sprite_scale), 8),
        )
        self.sprite = _get_arrow_sprite(sprite_size)

    def update(self, dt, game_scene):
        if self.is_dead:
            return

        step = self.direction * (self.speed * dt)
        next_x = self.position.x + step.x
        next_y = self.position.y + step.y
        if game_scene.collision_system.check_collision(
            next_x - self.radius,
            next_y - self.radius,
            self.collision_probe,
        ):
            self.is_dead = True
            return

        self.position.x = next_x
        self.position.y = next_y
        self.travelled_distance += step.length()

        projectile_rect = (
            self.position.x - self.radius,
            self.position.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )
        for enemy in game_scene.enemies:
            if enemy.is_dead or not rects_intersect(projectile_rect, enemy.get_hurtbox_rect()):
                continue
            if enemy.take_damage(self.damage, "ranged"):
                enemy.apply_hit_reaction(self.direction, 18.0, 0.08)
                game_scene._spawn_damage_number(enemy, enemy.last_damage_taken)
                game_scene._trigger_hit_feedback(SimpleNamespace(kind="light"))
            self.is_dead = True
            return

        if self.travelled_distance >= self.max_distance:
            self.is_dead = True

    def draw(self, screen, camera):
        if self.is_dead:
            return
        x = int(self.position.x - camera.position.x)
        y = int(self.position.y - camera.position.y)
        if self.sprite is not None:
            angle = -math.degrees(math.atan2(self.direction.y, self.direction.x))
            sprite = pygame.transform.rotate(self.sprite, angle)
            rect = sprite.get_rect(center=(x, y))
            screen.blit(sprite, rect.topleft)
            return
        pygame.draw.circle(screen, (150, 220, 255), (x, y), self.radius)
        pygame.draw.circle(screen, COLORS["BLACK"], (x, y), self.radius, width=1)


class _ProjectileProbe:
    def __init__(self, radius):
        self.size = radius * 2

    def get_hitbox_at(self, x, y):
        return (x, y, self.size, self.size)
