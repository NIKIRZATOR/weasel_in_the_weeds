from __future__ import annotations

import pygame

from game.core.timer import Timer
from game.core.vector import Vector2
from game.entities.entity import Entity
from settings import COLORS, SHOW_INTERACTION_ZONES


class Enemy(Entity):
    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="enemy",
        max_health=20,
        speed=80,
        damage=4,
        attack_cooldown=1.0,
        detection_radius=160,
        color=None,
    ):
        super().__init__(x, y, width, height)
        self.name = name
        self.max_health = max(1, int(max_health))
        self.health = self.max_health
        self.speed = max(0, int(speed))
        self.damage = max(0, int(damage))
        self.attack_cooldown = Timer(float(attack_cooldown))
        self.detection_radius = max(self.width, int(detection_radius))
        self.attack_radius = None
        self.color = COLORS["UI_SLOT_SELECTED"] if color is None else color
        self.facing_left = False
        self.is_dead = False

    def take_damage(self, damage):
        amount = max(1, int(damage))
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.is_dead = True
        return True

    def update(self, dt, game_scene):
        if self.is_dead:
            return
        self.attack_cooldown.update(dt)

    def _move_towards(self, target_x, target_y, dt, game_scene):
        dx = target_x - self.position.x
        dy = target_y - self.position.y
        direction = Vector2(dx, dy)
        if direction.length() == 0:
            return

        direction = direction.normalize()
        move_x = direction.x * self.speed * dt
        move_y = direction.y * self.speed * dt
        self._move_with_collision(move_x, move_y, game_scene)
        if move_x != 0:
            self.facing_left = move_x < 0

    def _move_away_from(self, target_x, target_y, dt, game_scene):
        dx = self.position.x - target_x
        dy = self.position.y - target_y
        direction = Vector2(dx, dy)
        if direction.length() == 0:
            return

        direction = direction.normalize()
        move_x = direction.x * self.speed * dt
        move_y = direction.y * self.speed * dt
        self._move_with_collision(move_x, move_y, game_scene)
        if move_x != 0:
            self.facing_left = move_x < 0

    def _move_with_collision(self, move_x, move_y, game_scene):
        if move_x != 0:
            new_x = self.position.x + move_x
            if not game_scene.check_collision(new_x, self.position.y, self):
                self.position.x = new_x
        if move_y != 0:
            new_y = self.position.y + move_y
            if not game_scene.check_collision(self.position.x, new_y, self):
                self.position.y = new_y

    def _draw_health_bar(self, screen, camera):
        bar_width = self.width
        bar_height = 6
        x = self.position.x - camera.position.x
        y = self.position.y - camera.position.y - 12
        ratio = self.health / self.max_health if self.max_health > 0 else 0

        pygame.draw.rect(screen, (70, 20, 20), (x, y, bar_width, bar_height), border_radius=3)
        pygame.draw.rect(screen, (220, 70, 70), (x, y, bar_width * ratio, bar_height), border_radius=3)
        pygame.draw.rect(screen, COLORS["BLACK"], (x, y, bar_width, bar_height), width=1, border_radius=3)

    def _draw_body(self, screen, camera):
        x = self.position.x - camera.position.x
        y = self.position.y - camera.position.y
        pygame.draw.rect(screen, self.color, (x, y, self.width, self.height), border_radius=6)
        pygame.draw.rect(screen, COLORS["BLACK"], (x, y, self.width, self.height), width=2, border_radius=6)

        dot_color = COLORS["BLACK"]
        pygame.draw.circle(screen, dot_color, (int(x + self.width * 0.32), int(y + self.height * 0.34)), 3)
        pygame.draw.circle(screen, dot_color, (int(x + self.width * 0.68), int(y + self.height * 0.34)), 3)
        pygame.draw.circle(screen, dot_color, (int(x + self.width * 0.5), int(y + self.height * 0.68)), 3)

    def _draw_zone(self, screen, camera, radius, fill_color, border_color, alpha, border_width=2):
        hitbox_x, hitbox_y, hitbox_w, hitbox_h = self.get_hitbox_rect()
        padding = int(radius)
        rect = pygame.Rect(
            int(hitbox_x - padding - camera.position.x),
            int(hitbox_y - padding - camera.position.y),
            int(hitbox_w + padding * 2),
            int(hitbox_h + padding * 2),
        )
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        border_radius = min(padding, rect.width // 2, rect.height // 2)
        pygame.draw.rect(
            overlay,
            (*fill_color, alpha),
            overlay.get_rect(),
            border_radius=border_radius,
        )
        pygame.draw.rect(
            overlay,
            border_color,
            overlay.get_rect(),
            width=border_width,
            border_radius=border_radius,
        )
        screen.blit(overlay, rect.topleft)

    def _draw_detection_zone(self, screen, camera):
        if not SHOW_INTERACTION_ZONES:
            return
        self._draw_zone(screen, camera, self.detection_radius, (255, 80, 80), COLORS["INTERACTION_ZONE"], 28)

    def _draw_attack_zone(self, screen, camera):
        if not SHOW_INTERACTION_ZONES or self.attack_radius is None:
            return
        self._draw_zone(screen, camera, self.attack_radius, (255, 200, 80), (255, 220, 120), 22, border_width=2)

    def draw_debug(self, screen, camera):
        self._draw_detection_zone(screen, camera)
        self._draw_attack_zone(screen, camera)
        super().draw_debug(screen, camera)

    def draw(self, screen, camera):
        if self.is_dead:
            return
        self._draw_health_bar(screen, camera)
        self._draw_body(screen, camera)
        self.draw_debug(screen, camera)



class MeleeEnemy(Enemy):
    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="melee_enemy",
        max_health=20,
        speed=75,
        damage=6,
        melee_range=50,
        detection_radius=150,
        attack_cooldown=1.0,
    ):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            max_health=max_health,
            speed=speed,
            damage=damage,
            attack_cooldown=attack_cooldown,
            detection_radius=detection_radius,
            color=(220, 55, 55),
        )
        self.melee_range = float(melee_range)
        self.attack_radius = self.melee_range

    def update(self, dt, game_scene):
        super().update(dt, game_scene)
        if self.is_dead:
            return

        player = game_scene.player
        player_center = player.get_center()
        distance = _rect_distance(self.get_hitbox_rect(), player.get_hitbox_rect())

        if distance > self.detection_radius:
            return

        if distance <= self.melee_range:
            if not self.attack_cooldown.is_active():
                player.take_damage(self.damage)
                self.attack_cooldown.start()
            return

        self._move_towards(player_center.x, player_center.y, dt, game_scene)


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
        probe = _ProjectileProbe(self.radius)

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
        if _rects_intersect(projectile_rect, player.get_hitbox_rect()):
            player.take_damage(self.damage)
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


class RangedEnemy(Enemy):
    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="ranged_enemy",
        max_health=14,
        speed=60,
        damage=4,
        preferred_distance=180,
        min_distance=120,
        attack_range=260,
        detection_radius=280,
        projectile_speed=260,
        projectile_radius=5,
        attack_cooldown=1.4,
    ):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            max_health=max_health,
            speed=speed,
            damage=damage,
            attack_cooldown=attack_cooldown,
            detection_radius=detection_radius,
            color=(200, 35, 35),
        )
        self.preferred_distance = float(preferred_distance)
        self.min_distance = float(min_distance)
        self.attack_range = float(attack_range)
        self.attack_radius = self.attack_range
        self.projectile_speed = float(projectile_speed)
        self.projectile_radius = int(projectile_radius)
        self.projectiles = []

    def update(self, dt, game_scene):
        super().update(dt, game_scene)
        if self.is_dead:
            return

        player = game_scene.player
        player_center = player.get_center()
        distance = _rect_distance(self.get_hitbox_rect(), player.get_hitbox_rect())

        if distance > self.detection_radius:
            self._update_projectiles(dt, game_scene)
            return

        if distance > self.preferred_distance:
            self._move_towards(player_center.x, player_center.y, dt, game_scene)
        elif distance < self.min_distance:
            self._move_away_from(player_center.x, player_center.y, dt, game_scene)

        if distance <= self.attack_range and not self.attack_cooldown.is_active():
            self._shoot(player_center.x, player_center.y)
            self.attack_cooldown.start()

        self._update_projectiles(dt, game_scene)

    def _shoot(self, target_x, target_y):
        origin = self.get_center()
        self.projectiles.append(
            RangedProjectile(
                origin.x,
                origin.y,
                target_x,
                target_y,
                self.projectile_speed,
                self.damage,
                self.projectile_radius,
            )
        )

    def _update_projectiles(self, dt, game_scene):
        alive_projectiles = []
        for projectile in self.projectiles:
            projectile.update(dt, game_scene)
            if not projectile.is_dead:
                alive_projectiles.append(projectile)
        self.projectiles = alive_projectiles

    def _draw_projectiles(self, screen, camera):
        for projectile in self.projectiles:
            projectile.draw(screen, camera)

    def draw(self, screen, camera):
        if self.is_dead:
            return
        self._draw_projectiles(screen, camera)
        super().draw(screen, camera)


def _rects_intersect(rect_a, rect_b):
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def _rect_distance(rect_a, rect_b):
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b

    dx = max(bx - (ax + aw), ax - (bx + bw), 0)
    dy = max(by - (ay + ah), ay - (by + bh), 0)
    return (dx * dx + dy * dy) ** 0.5


class _ProjectileProbe:
    def __init__(self, radius):
        self.radius = radius * 2

    def get_hitbox_at(self, x, y):
        return (x, y, self.radius, self.radius)
