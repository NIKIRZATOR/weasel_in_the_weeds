from __future__ import annotations

import pygame

from game.core.vector import Vector2
from game.entities.enemies.ai.steering import rects_intersect
from settings import COLORS


class EnemyProjectileProbe:
    def __init__(self, radius):
        self.radius = radius * 2

    def get_hitbox_at(self, x, y):
        return (x, y, self.radius, self.radius)


class RangedProjectile:
    def __init__(self, x, y, target_x, target_y, speed, damage, radius=5):
        self.position = Vector2(x, y)
        self.speed = float(speed)
        self.damage = max(1, int(damage))
        self.radius = int(radius)
        self.is_dead = False
        direction = Vector2(target_x - x, target_y - y)
        self.direction = direction.normalize() if direction.length() > 0 else Vector2(0, 0)
        self.travelled_distance = 0.0
        self.max_distance = 520.0

    def update(self, dt, game_scene):
        if self.is_dead:
            return

        step = self.direction * (self.speed * dt)
        next_x = self.position.x + step.x
        next_y = self.position.y + step.y
        probe = EnemyProjectileProbe(self.radius)

        if game_scene.collision_system.check_collision(next_x - self.radius, next_y - self.radius, probe):
            self.is_dead = True
            return

        self.position.x = next_x
        self.position.y = next_y
        self.travelled_distance += step.length()

        player = game_scene.player
        projectile_rect = pygame.Rect(
            int(self.position.x - self.radius),
            int(self.position.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )
        if rects_intersect(projectile_rect, player.get_hitbox_rect()):
            if player.take_damage(self.damage):
                self.on_hit_player(player)
            self.is_dead = True
            return

        if self.travelled_distance >= self.max_distance:
            self.is_dead = True

    def draw(self, screen, camera):
        if self.is_dead:
            return

        x = int(self.position.x - camera.position.x)
        y = int(self.position.y - camera.position.y)
        pygame.draw.circle(screen, (255, 190, 70), (x, y), self.radius)
        pygame.draw.circle(screen, COLORS["BLACK"], (x, y), self.radius, width=1)
        pygame.draw.circle(screen, (90, 20, 20), (x - 1, y - 1), max(1, self.radius // 2))

    def on_hit_player(self, player):
        return None


class SpikeProjectile(RangedProjectile):
    def __init__(self, x, y, dir_x, dir_y, speed, damage, radius=6):
        super().__init__(x, y, x + dir_x, y + dir_y, speed, damage, radius)

    def draw(self, screen, camera):
        if self.is_dead:
            return

        x = int(self.position.x - camera.position.x)
        y = int(self.position.y - camera.position.y)
        direction = self.direction
        tip_x = x + int(direction.x * (self.radius + 6))
        tip_y = y + int(direction.y * (self.radius + 6))
        side_x = int(-direction.y * max(2, self.radius // 2))
        side_y = int(direction.x * max(2, self.radius // 2))
        points = [
            (tip_x, tip_y),
            (x - int(direction.x * self.radius) + side_x, y - int(direction.y * self.radius) + side_y),
            (x - int(direction.x * self.radius) - side_x, y - int(direction.y * self.radius) - side_y),
        ]
        pygame.draw.polygon(screen, (220, 240, 210), points)
        pygame.draw.polygon(screen, COLORS["BLACK"], points, width=1)
