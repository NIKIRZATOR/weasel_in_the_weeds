from __future__ import annotations

import math

import pygame

from game.core.timer import Timer
from game.core.vector import Vector2
from game.effects import EffectType
from game.entities.enemies.ai.states import CHASE
from game.entities.enemies.ai.steering import entity_distance, rects_intersect
from game.entities.enemies.base import Enemy
from game.entities.enemies.projectiles import EnemyProjectileProbe, RangedProjectile
from settings import ASSETS_DIR, COLORS


class SpiderEnemy(Enemy):
    SPRITE_FRAME_SIZE = (64, 64)
    SPRITE_FRAME_DURATIONS = {
        "idle": 0.14,
        "move": 0.12,
        "attack": 0.08,
        "web_attack": 0.1,
    }
    SPRITE_NATIVE_FACING_LEFT = {
        "idle": False,
        "move": False,
        "attack": False,
        "web_attack": False,
    }
    SPRITE_ANIMATIONS = {
        "idle": (ASSETS_DIR / "enemies" / "spider" / "spider_idle.png", 8),
        "move": (ASSETS_DIR / "enemies" / "spider" / "spider_steps.png", 3),
        "attack": (ASSETS_DIR / "enemies" / "spider" / "spider_attack.png", 4),
        "web_attack": (ASSETS_DIR / "enemies" / "spider" / "spider_web_attack.png", 2),
    }
    BODY_HITBOX = {
        "width": 20,
        "height": 16,
        "offset_x": 6,
        "offset_y": 12,
    }
    HURTBOX = {
        "width": 18,
        "height": 16,
        "offset_x": 7,
        "offset_y": 12,
    }
    ATTACK_HITBOX = {
        "width": 18,
        "height": 12,
        "offset_x": 18,
        "offset_y": 14,
        "mirror_with_facing": True,
    }
    COLLISION_CIRCLE = {
        "radius": 10,
    }
    LOOT_TABLE = (
        {"item_id": "web", "min_quantity": 1, "max_quantity": 2, "chance": 0.75},
        {"item_id": "knowledge_shard", "min_quantity": 1, "max_quantity": 1, "chance": 0.18},
        {"coins": 4, "chance": 0.45},
    )

    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="spider_enemy",
        max_health=18,
        speed=92,
        damage=5,
        melee_range=24,
        leap_range=150,
        leap_min_range=64,
        leap_speed=360,
        leap_duration=0.28,
        spit_range=250,
        projectile_speed=290,
        projectile_radius=6,
        slow_amount=0.22,
        slow_duration=2.6,
        attack_cooldown=1.1,
        detection_radius=260,
        patrol_radius=150,
        patrol_idle_min=0.35,
        patrol_idle_max=0.9,
        linger_duration=1.0,
        xp_reward=12,
        **hitbox_kwargs,
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
            patrol_radius=patrol_radius,
            patrol_idle_min=patrol_idle_min,
            patrol_idle_max=patrol_idle_max,
            linger_duration=linger_duration,
            color=(72, 62, 85),
            xp_reward=xp_reward,
            **hitbox_kwargs,
        )
        self.melee_range = float(melee_range)
        self.leap_range = float(leap_range)
        self.leap_min_range = float(leap_min_range)
        self.leap_speed = float(leap_speed)
        self.leap_duration = max(0.05, float(leap_duration))
        self.spit_range = float(spit_range)
        self.projectile_speed = float(projectile_speed)
        self.projectile_radius = int(projectile_radius)
        self.slow_amount = max(0.0, float(slow_amount))
        self.slow_duration = max(0.0, float(slow_duration))
        self.attack_radius = self.spit_range
        self.projectiles = []
        self.leap_timer = Timer(self.leap_duration)
        self.leap_direction = Vector2()
        self.leap_damage_applied = False
        self.attack_animation_timer = 0.0
        self.web_attack_animation_timer = 0.0

    def update(self, dt, game_scene):
        previous_position = Vector2(self.position.x, self.position.y)
        super().update(dt, game_scene)
        if self.is_dead:
            return

        self._update_projectiles(dt, game_scene)
        if self.leap_timer.is_active():
            self._update_leap(dt, game_scene)
        elif self.behavior_state == CHASE:
            player = game_scene.player
            player_center = player.get_center()
            distance = entity_distance(self, player)

            if distance <= self.melee_range and not self.attack_cooldown.is_active():
                self._bite(player)
            elif (
                self.leap_min_range <= distance <= self.leap_range
                and not self.attack_cooldown.is_active()
                and self._has_clear_lane(player_center)
            ):
                self._start_leap(player_center)
            elif distance <= self.spit_range and not self.attack_cooldown.is_active():
                self._spit(player_center.x, player_center.y)
                self.attack_cooldown.start()
            else:
                chase_start = Vector2(self.position.x, self.position.y)
                self._move_towards(player_center.x, player_center.y, dt, game_scene, use_pathfinding=True)
                self._update_stuck_state(dt, chase_start, game_scene)

        moved = (self.position.x != previous_position.x) or (self.position.y != previous_position.y)
        self.attack_animation_timer = max(0.0, self.attack_animation_timer - dt)
        self.web_attack_animation_timer = max(0.0, self.web_attack_animation_timer - dt)
        self._update_animation(dt, moved)

    def _bite(self, player):
        self.activate_attack_hitbox(duration=0.12)
        attack_direction = Vector2(player.get_center().x - self.get_center().x, player.get_center().y - self.get_center().y)
        player.take_damage(self.damage, direction=attack_direction, force=75.0, stun_duration=0.12)
        self.attack_cooldown.start()
        self.attack_animation_timer = max(self.attack_animation_timer, 0.18)

    def _spit(self, target_x, target_y):
        origin = self.get_center()
        if hasattr(self, "game_scene") and self.game_scene is not None and self.game_scene._is_enemy_audible(self):
            self.game_scene.app.audio.play_sound("spider_web_attack", volume=0.56)
        self.projectiles.append(
            WebProjectile(
                origin.x,
                origin.y,
                target_x,
                target_y,
                self.projectile_speed,
                self.damage,
                radius=self.projectile_radius,
                slow_amount=self.slow_amount,
                slow_duration=self.slow_duration,
            )
        )
        self.web_attack_animation_timer = max(self.web_attack_animation_timer, 0.18)

    def _start_leap(self, player_center):
        direction = Vector2(player_center.x - self.get_center().x, player_center.y - self.get_center().y)
        if direction.length() <= 0:
            return
        self.leap_direction = direction.normalize()
        self.leap_timer.start(self.leap_duration)
        self.stun_timer = max(self.stun_timer, self.leap_duration)
        self.leap_damage_applied = False
        self.attack_cooldown.start(max(self.attack_cooldown.duration, self.leap_duration + 0.45))
        self._update_facing_from_direction(self.leap_direction)
        self.attack_animation_timer = max(self.attack_animation_timer, self.leap_duration)

    def _update_leap(self, dt, game_scene):
        step = self.leap_direction * (self.leap_speed * dt)
        self._move_with_collision(step.x, step.y, game_scene)
        player = game_scene.player
        if not self.leap_damage_applied and rects_intersect(self.get_hitbox_rect(), player.get_hitbox_rect()):
            player.take_damage(self.damage + 1, direction=self.leap_direction, force=140.0, stun_duration=0.18)
            self.leap_damage_applied = True
        if self.leap_timer.update(dt):
            self.leap_damage_applied = False

    def _has_clear_lane(self, player_center):
        offset = player_center - self.get_center()
        return abs(offset.x) >= self.width * 0.35 or abs(offset.y) >= self.height * 0.35

    def _update_projectiles(self, dt, game_scene):
        alive_projectiles = []
        for projectile in self.projectiles:
            projectile.update(dt, game_scene)
            if not projectile.is_dead:
                alive_projectiles.append(projectile)
        self.projectiles = alive_projectiles

    def draw(self, screen, camera):
        if self.is_dead:
            return
        for projectile in self.projectiles:
            projectile.draw(screen, camera)
        super().draw(screen, camera)

    def _resolve_animation_name(self, moved):
        if self.web_attack_animation_timer > 0.0:
            return "web_attack"
        if self.attack_animation_timer > 0.0 or self.leap_timer.is_active():
            return "attack"
        if moved:
            return "move"
        return "idle"


class WebProjectile(RangedProjectile):
    def __init__(
        self,
        x,
        y,
        target_x,
        target_y,
        speed,
        damage,
        radius=6,
        slow_amount=0.25,
        slow_duration=2.6,
    ):
        super().__init__(x, y, target_x, target_y, speed, damage, radius)
        self.slow_amount = max(0.0, float(slow_amount))
        self.slow_duration = max(0.0, float(slow_duration))

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
            hit_direction = Vector2(player.get_center().x - self.position.x, player.get_center().y - self.position.y)
            player.take_damage(self.damage, direction=hit_direction, force=60.0, stun_duration=0.12)
            player.add_active_effect(EffectType.SLOWED, self.slow_amount, self.slow_duration)
            self.is_dead = True
            return

        if self.travelled_distance >= self.max_distance:
            self.is_dead = True

    def draw(self, screen, camera):
        if self.is_dead:
            return

        x = int(self.position.x - camera.position.x)
        y = int(self.position.y - camera.position.y)
        pygame.draw.circle(screen, (230, 235, 245), (x, y), self.radius)
        pygame.draw.circle(screen, COLORS["BLACK"], (x, y), self.radius, width=1)
        for angle in (0, math.pi / 3, 2 * math.pi / 3):
            dx = int(math.cos(angle) * (self.radius + 3))
            dy = int(math.sin(angle) * (self.radius + 3))
            pygame.draw.line(screen, (180, 185, 210), (x - dx, y - dy), (x + dx, y + dy), width=1)
