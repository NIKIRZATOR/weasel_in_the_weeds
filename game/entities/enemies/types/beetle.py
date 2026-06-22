from __future__ import annotations

import pygame

from game.core.timer import Timer
from game.core.vector import Vector2
from game.entities.enemies.ai.states import CHASE
from game.entities.enemies.ai.steering import entity_distance, rects_intersect
from game.entities.enemies.base import Enemy
from settings import COLORS


class BeetleEnemy(Enemy):
    BODY_HITBOX = {
        "width": 22,
        "height": 18,
        "offset_x": 5,
        "offset_y": 11,
    }
    HURTBOX = {
        "width": 20,
        "height": 18,
        "offset_x": 6,
        "offset_y": 11,
    }
    ATTACK_HITBOX = {
        "width": 20,
        "height": 14,
        "offset_x": 18,
        "offset_y": 13,
        "mirror_with_facing": True,
    }
    COLLISION_CIRCLE = {
        "radius": 11,
    }
    LOOT_TABLE = (
        {"item_id": "stone_pebble", "min_quantity": 1, "max_quantity": 2, "chance": 0.7},
        {"item_id": "beetle_charm", "min_quantity": 1, "max_quantity": 1, "chance": 0.12},
        {"coins": 5, "chance": 0.5},
    )

    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="beetle_enemy",
        max_health=34,
        speed=64,
        damage=7,
        melee_range=26,
        charge_range=210,
        charge_min_range=70,
        charge_speed=260,
        charge_duration=0.5,
        shell_duration=2.4,
        shell_cooldown=7.5,
        shell_regen_per_second=4.5,
        shell_trigger_health_ratio=0.45,
        shell_damage_multiplier=0.35,
        attack_cooldown=1.0,
        detection_radius=230,
        patrol_radius=140,
        patrol_idle_min=0.45,
        patrol_idle_max=1.0,
        linger_duration=1.0,
        xp_reward=16,
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
            color=(132, 86, 42),
            xp_reward=xp_reward,
            **hitbox_kwargs,
        )
        self.melee_range = float(melee_range)
        self.charge_range = float(charge_range)
        self.charge_min_range = float(charge_min_range)
        self.charge_speed = float(charge_speed)
        self.charge_duration = max(0.08, float(charge_duration))
        self.attack_radius = self.charge_range
        self.charge_timer = Timer(self.charge_duration)
        self.charge_direction = Vector2()
        self.charge_hit_applied = False
        self.shell_duration = max(0.1, float(shell_duration))
        self.shell_timer = Timer(self.shell_duration)
        self.shell_cooldown = Timer(float(shell_cooldown))
        self.shell_regen_per_second = max(0.0, float(shell_regen_per_second))
        self.shell_trigger_health_ratio = min(1.0, max(0.05, float(shell_trigger_health_ratio)))
        self.shell_damage_multiplier = min(1.0, max(0.0, float(shell_damage_multiplier)))

    def take_damage(self, damage, attack_kind=None):
        if self.shell_timer.is_active():
            damage = max(1, int(round(float(damage) * self.shell_damage_multiplier)))
        return super().take_damage(damage, attack_kind=attack_kind)

    def update(self, dt, game_scene):
        super().update(dt, game_scene)
        if self.is_dead:
            return

        if self.shell_cooldown.is_active():
            self.shell_cooldown.update(dt)
        if self.charge_timer.is_active():
            self._update_charge(dt, game_scene)
            return
        if self.shell_timer.is_active():
            self._update_shell(dt)
            return
        if self.behavior_state != CHASE:
            return

        if self._should_enter_shell():
            self._start_shell()
            return

        player = game_scene.player
        player_center = player.get_center()
        distance = entity_distance(self, player)

        if distance <= self.melee_range and not self.attack_cooldown.is_active():
            self._bite(player)
            return

        if self.charge_min_range <= distance <= self.charge_range and not self.attack_cooldown.is_active():
            self._start_charge(player_center)
            return

        previous_position = Vector2(self.position.x, self.position.y)
        self._move_towards(player_center.x, player_center.y, dt, game_scene, use_pathfinding=True)
        self._update_stuck_state(dt, previous_position, game_scene)

    def _should_enter_shell(self):
        return (
            not self.shell_cooldown.is_active()
            and self.health > 0
            and self.health <= self.max_health * self.shell_trigger_health_ratio
            and self.health < self.max_health
        )

    def _start_shell(self):
        self.shell_timer.start(self.shell_duration)
        self.shell_cooldown.start()
        self.stun_timer = max(self.stun_timer, self.shell_duration)
        self.attack_cooldown.start(max(self.attack_cooldown.duration, self.shell_duration + 0.25))

    def _update_shell(self, dt):
        self.health = min(self.max_health, self.health + self.shell_regen_per_second * dt)
        self.shell_timer.update(dt)

    def _start_charge(self, player_center):
        direction = Vector2(player_center.x - self.get_center().x, player_center.y - self.get_center().y)
        if direction.length() <= 0:
            return
        self.charge_direction = direction.normalize()
        self._update_facing_from_direction(self.charge_direction)
        self.charge_timer.start(self.charge_duration)
        self.stun_timer = max(self.stun_timer, self.charge_duration)
        self.attack_cooldown.start(max(self.attack_cooldown.duration, self.charge_duration + 0.5))
        self.charge_hit_applied = False

    def _update_charge(self, dt, game_scene):
        step = self.charge_direction * (self.charge_speed * dt)
        previous_x = self.position.x
        previous_y = self.position.y
        self._move_with_collision(step.x, step.y, game_scene)

        player = game_scene.player
        if not self.charge_hit_applied and rects_intersect(self.get_hitbox_rect(), player.get_hitbox_rect()):
            player.take_damage(self.damage + 2, direction=self.charge_direction, force=180.0, stun_duration=0.22)
            self.charge_hit_applied = True

        blocked = abs(self.position.x - previous_x) < 0.01 and abs(self.position.y - previous_y) < 0.01
        if blocked:
            self.charge_timer.active = False
        else:
            self.charge_timer.update(dt)

    def _bite(self, player):
        self.activate_attack_hitbox(duration=0.12)
        direction = Vector2(player.get_center().x - self.get_center().x, player.get_center().y - self.get_center().y)
        player.take_damage(self.damage, direction=direction, force=95.0, stun_duration=0.14)
        self.attack_cooldown.start()

    def _draw_body(self, screen, camera):
        x = self.position.x - camera.position.x
        y = self.position.y - camera.position.y
        shell_active = self.shell_timer.is_active()
        body_color = (232, 220, 205) if self.hurt_flash_timer > 0 else self.color
        shell_color = (88, 64, 30) if not shell_active else (60, 92, 118)
        pygame.draw.ellipse(screen, shell_color, (x + 4, y + 6, self.width - 8, self.height - 8))
        pygame.draw.ellipse(screen, COLORS["BLACK"], (x + 4, y + 6, self.width - 8, self.height - 8), width=2)
        pygame.draw.ellipse(screen, body_color, (x + 10, y + 14, self.width - 20, self.height - 16))
        pygame.draw.ellipse(screen, COLORS["BLACK"], (x + 10, y + 14, self.width - 20, self.height - 16), width=1)
        horn_color = (210, 190, 120)
        left_horn = [(x + self.width * 0.3, y + self.height * 0.2), (x + self.width * 0.18, y + self.height * 0.05), (x + self.width * 0.36, y + self.height * 0.16)]
        right_horn = [(x + self.width * 0.7, y + self.height * 0.2), (x + self.width * 0.82, y + self.height * 0.05), (x + self.width * 0.64, y + self.height * 0.16)]
        pygame.draw.polygon(screen, horn_color, left_horn)
        pygame.draw.polygon(screen, horn_color, right_horn)
        pygame.draw.polygon(screen, COLORS["BLACK"], left_horn, width=1)
        pygame.draw.polygon(screen, COLORS["BLACK"], right_horn, width=1)
