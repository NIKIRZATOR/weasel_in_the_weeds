from __future__ import annotations

import random

import pygame

from game.core.vector import Vector2
from game.entities.enemies.ai.behaviors import can_detect_player
from game.entities.enemies.ai.steering import point_distance
from game.entities.enemies.base import Enemy
from settings import COLORS


class BaseBossEnemy(Enemy):
    PHASE_TWO_HEALTH_RATIO = 0.5

    def __init__(
        self,
        x,
        y,
        width,
        height,
        *,
        boss_name=None,
        phase_two_health_ratio=None,
        **kwargs,
    ):
        super().__init__(x, y, width, height, **kwargs)
        self.boss_name = boss_name or self.name
        self.phase = 1
        self.encounter_started = False
        self.phase_two_health_ratio = float(
            self.PHASE_TWO_HEALTH_RATIO if phase_two_health_ratio is None else phase_two_health_ratio
        )
        self.action_state = "idle"
        self.action_timer = 0.0
        self.state_clock = 0.0
        self.combat_cooldowns = {}
        self.strafe_clockwise = random.choice((True, False))
        self.strafe_swap_timer = random.uniform(1.1, 2.4)
        self.phase_transition_timer = 0.0
        self.velocity_intent = Vector2(0, 0)

    def update(self, dt, game_scene):
        if self.is_dead:
            return

        self._update_common_timers(dt)
        if self.is_dead:
            return
        if self._update_knockback(dt, game_scene):
            return
        if self.stun_timer > 0:
            self.stun_timer = max(0.0, self.stun_timer - dt)
            return

        self.state_clock += dt
        self._tick_action_timer(dt)
        self._tick_combat_cooldowns(dt)
        self._update_phase_state()

        player = game_scene.player
        player_center = player.get_center()
        distance_to_player = point_distance(self.get_center(), player_center)
        if can_detect_player(self, player, distance_to_player):
            self.encounter_started = True
        if not self.encounter_started:
            return

        self._update_boss(dt, game_scene, player, distance_to_player)

    def _update_common_timers(self, dt):
        self.attack_cooldown.update(dt)
        if self.attack_hitbox_timer.update(dt):
            self.attack_hitbox_active = False
        self.stuck_repath_cooldown = max(0.0, self.stuck_repath_cooldown - dt)
        self.hurt_flash_timer = max(0.0, self.hurt_flash_timer - dt)

    def _tick_action_timer(self, dt):
        if self.action_timer > 0:
            self.action_timer = max(0.0, self.action_timer - dt)

    def _tick_combat_cooldowns(self, dt):
        expired = []
        for key, value in self.combat_cooldowns.items():
            next_value = max(0.0, value - dt)
            self.combat_cooldowns[key] = next_value
            if next_value == 0.0:
                expired.append(key)
        for key in expired:
            self.combat_cooldowns.pop(key, None)

    def _update_phase_state(self):
        if self.phase >= 2:
            return
        health_ratio = self.health / self.max_health if self.max_health > 0 else 0.0
        if health_ratio > self.phase_two_health_ratio:
            return
        self.phase = 2
        self.phase_transition_timer = max(self.phase_transition_timer, 0.9)
        self.on_phase_changed(2)

    def on_phase_changed(self, new_phase):
        pass

    def apply_hit_reaction(self, direction, force=0.0, stun=0.0):
        # Bosses still take damage and flash on hit, but player attacks do not
        # stun them, push them, or cancel their current action state.
        return

    def set_action(self, action_state, duration=0.0):
        self.action_state = action_state
        self.action_timer = max(0.0, float(duration))
        self.state_clock = 0.0

    def set_cooldown(self, key, duration):
        self.combat_cooldowns[key] = max(0.0, float(duration))

    def cooldown_ready(self, key):
        return self.combat_cooldowns.get(key, 0.0) <= 0.0

    def face_towards(self, target):
        direction = Vector2(target.x - self.get_center().x, target.y - self.get_center().y)
        if direction.length() > 0:
            self._update_facing_from_direction(direction)
        return direction

    def move_orbit(self, target_x, target_y, dt, game_scene, desired_distance, speed_scale=1.0):
        center = self.get_center()
        radial = Vector2(target_x - center.x, target_y - center.y)
        if radial.length() == 0:
            return
        radial = radial.normalize()
        tangent = Vector2(-radial.y, radial.x) if self.strafe_clockwise else Vector2(radial.y, -radial.x)
        distance = point_distance(center, Vector2(target_x, target_y))
        radial_weight = max(-0.8, min(0.8, (distance - desired_distance) / max(24.0, desired_distance)))
        direction = (tangent + radial * radial_weight).normalize()
        speed = self.speed * speed_scale
        self._move_with_collision(direction.x * speed * dt, direction.y * speed * dt, game_scene)
        self._update_facing_from_direction(direction)

    def move_evade(self, target_x, target_y, dt, game_scene, speed_scale=1.25):
        center = self.get_center()
        away = Vector2(center.x - target_x, center.y - target_y)
        if away.length() == 0:
            away = Vector2(-1 if self.facing_left else 1, 0)
        away = away.normalize()
        tangent = Vector2(-away.y, away.x) if self.strafe_clockwise else Vector2(away.y, -away.x)
        direction = (away * 0.72 + tangent * 0.92).normalize()
        speed = self.speed * speed_scale
        self._move_with_collision(direction.x * speed * dt, direction.y * speed * dt, game_scene)
        self._update_facing_from_direction(direction)

    def _draw_health_bar(self, screen, camera):
        bar_width = max(self.width * 2.2, 140)
        bar_height = 10
        x = self.position.x + self.width / 2 - bar_width / 2 - camera.position.x
        y = self.position.y - 24 - camera.position.y
        ratio = self.health / self.max_health if self.max_health > 0 else 0
        phase_color = (220, 90, 60) if self.phase == 1 else (120, 185, 235)
        pygame.draw.rect(screen, (40, 18, 18), (x, y, bar_width, bar_height), border_radius=5)
        pygame.draw.rect(screen, phase_color, (x, y, bar_width * ratio, bar_height), border_radius=5)
        pygame.draw.rect(screen, COLORS["BLACK"], (x, y, bar_width, bar_height), width=2, border_radius=5)
        font = pygame.font.Font(None, 24)
        label = font.render(f"{self.boss_name} | P{self.phase}", True, COLORS["WHITE"])
        screen.blit(label, (x, y - 20))

    def _update_boss(self, dt, game_scene, player, distance_to_player):
        raise NotImplementedError
