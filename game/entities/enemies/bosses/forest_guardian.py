from __future__ import annotations

import math
import random

import pygame

from game.core.assets import load_image
from game.core.vector import Vector2
from game.entities.enemies.ai.steering import rects_intersect
from game.entities.enemies.bosses.base_boss import BaseBossEnemy
from game.entities.enemies.projectiles import SpikeProjectile
from settings import ASSETS_DIR, COLORS, SHOW_ENEMY_ATTACK_RADII, SHOW_INTERACTION_ZONES


class ForestGuardianBoss(BaseBossEnemy):
    PHASE_TWO_RANGED_RESISTANCE = 0.85
    SPRITE_FRAME_SIZE = (64, 64)
    SPRITE_ASSETS = {
        "idle": ("forest_guardian_idle.png", 1, 0.5),
        "move": ("forest_guardian_steps.png", 4, 0.14),
        "charge": ("forest_guardian_dash.png", 4, 0.09),
        "melee": ("forest_guardian_meele_attack.png", 5, 0.08),
    }
    SPRITE_NATIVE_FACING_LEFT = {
        "idle": False,
        "move": True,
        "charge": False,
        "melee": False,
    }
    BODY_HITBOX = {
        "width": 100,
        "height": 100,
        "offset_x": 16,
        "offset_y": 16,
    }
    HURTBOX = {
        "width": 100,
        "height": 100,
        "offset_x": 16,
        "offset_y": 16,
    }
    ATTACK_HITBOX = {
        "width": 90,
        "height": 90,
        "offset_x": 16,
        "offset_y": 16,
        "mirror_with_facing": True,
    }
    COLLISION_CIRCLE = {
        "radius": 16,
        "offset_x": 64,
        "offset_y": 64,
    }
    LOOT_TABLE = (
        {"item_id": "feather", "min_quantity": 2, "max_quantity": 4, "chance": 1.0},
        {"item_id": "bone", "min_quantity": 1, "max_quantity": 2, "chance": 0.8},
        {"knowledge_shards": 5, "chance": 1.0},
        {"coins": 14, "chance": 1.0},
    )

    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="forest_guardian",
        max_health=180,
        speed=88,
        damage=12,
        melee_range=66,
        charge_range=240,
        charge_speed=300,
        attack_cooldown=1.0,
        detection_radius=420,
        xp_reward=90,
        **hitbox_kwargs,
    ):
        width = max(int(width), 76)
        height = max(int(height), 64)
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            boss_name="Forest Guardian",
            max_health=max_health,
            speed=speed,
            damage=damage,
            attack_cooldown=attack_cooldown,
            detection_radius=detection_radius,
            patrol_radius=80,
            patrol_idle_min=0.2,
            patrol_idle_max=0.4,
            linger_duration=2.4,
            color=(122, 84, 50),
            xp_reward=xp_reward,
            phase_two_health_ratio=0.5,
            **hitbox_kwargs,
        )
        self.melee_range = float(melee_range)
        self.charge_range = float(charge_range)
        self.charge_speed = float(charge_speed)
        self.attack_radius = self.charge_range
        self.projectiles = []
        self.charge_direction = Vector2(1, 0)
        self.charge_time_left = 0.0
        self.charge_hit_player = False
        self.charge_duration = 0.62 * 1.5
        self.charge_speed_multiplier = 1.3
        self.volley_shots_remaining = 0
        self.volley_burst_timer = 0.0
        self.volley_spread_degrees = 30.0
        self.melee_damage_done = False
        self.phase_glow_timer = 0.0
        self.proximity_pressure_timer = 0.0
        self.shockwave_damage_done = False
        self.shockwave_committed = False
        self.shockwave_radius = 130.0
        self.shockwave_trigger_radius = 130.0
        self.shockwave_trigger_time = 1.5
        self.shockwave_windup_duration = 0.24
        self.shockwave_burst_duration = 0.12
        self.sprite_asset_dir = ASSETS_DIR / "bosses" / "forest_guardian"
        self.sprite_animations = self._load_sprite_animations()
        self.current_animation = "idle"
        self.current_frame_index = 0
        self.animation_frame_timer = 0.0
        self.current_sprite = self._get_animation_frame("idle", 0)

    def update(self, dt, game_scene):
        previous_position = Vector2(self.position.x, self.position.y)
        super().update(dt, game_scene)
        moved = (self.position.x != previous_position.x) or (self.position.y != previous_position.y)
        self._update_animation(dt, moved)

    def on_phase_changed(self, new_phase):
        self.set_action("phase_shift", 0.95)
        self.set_cooldown("melee", 0.6)
        self.set_cooldown("charge", 1.2)
        self.set_cooldown("spikes", 0.8)
        self.strafe_clockwise = not self.strafe_clockwise
        self.phase_glow_timer = 1.2

    def get_resistance(self, resistance_type):
        resistance = super().get_resistance(resistance_type)
        normalized_type = str(resistance_type).strip().lower()
        if self.phase >= 2 and normalized_type == "ranged":
            return max(resistance, self.PHASE_TWO_RANGED_RESISTANCE)
        return resistance

    def _update_boss(self, dt, game_scene, player, distance_to_player):
        self.phase_glow_timer = max(0.0, self.phase_glow_timer - dt)
        self._update_projectiles(dt, game_scene)
        player_center = player.get_center()
        self._update_proximity_pressure(dt, distance_to_player)

        if (
            self.action_state not in {"charge", "charge_windup", "shockwave_windup", "shockwave_burst", "spike_volley"}
            and self._try_trigger_shockwave()
        ):
            return

        if self.action_state == "phase_shift":
            self.face_towards(player_center)
            self.move_evade(player_center.x, player_center.y, dt, game_scene, speed_scale=0.95)
            if self.action_timer == 0.0:
                self.set_action("orbit", 0.85)
            return
        if self.action_state == "melee_windup":
            self._update_melee_windup(dt, game_scene, player)
            return
        if self.action_state == "charge_windup":
            self._update_charge_windup(dt, game_scene, player)
            return
        if self.action_state == "charge":
            self._update_charge(dt, game_scene, player)
            return
        if self.action_state == "shockwave_windup":
            self._update_shockwave_windup(dt, game_scene, player)
            return
        if self.action_state == "shockwave_burst":
            self._update_shockwave_burst(dt, game_scene, player)
            return
        if self.action_state == "spike_windup":
            self._update_spike_windup(dt, game_scene, player)
            return
        if self.action_state == "spike_volley":
            self._update_spike_volley(dt, game_scene, player)
            return
        if self.action_state == "recover":
            self._update_recover(dt, game_scene, player)
            return
        if self.action_state == "evade":
            self.move_evade(player_center.x, player_center.y, dt, game_scene, speed_scale=1.2)
            if self.action_timer == 0.0:
                self.set_action("orbit", 0.7)
            return
        if (
            player.is_attacking
            and distance_to_player <= 118
            and self.cooldown_ready("evade")
            and self.proximity_pressure_timer <= 0.0
        ):
            self.set_cooldown("evade", 2.2)
            self.strafe_clockwise = random.choice((True, False))
            self.set_action("evade", 0.42)
            return
        if self._try_start_attack(distance_to_player):
            return
        self._update_movement_brain(dt, game_scene, player_center, distance_to_player)

    def _update_proximity_pressure(self, dt, distance_to_player):
        if self.shockwave_committed or self.action_state in {"shockwave_windup", "shockwave_burst"}:
            return
        if distance_to_player <= self.shockwave_trigger_radius:
            self.proximity_pressure_timer += dt
        else:
            self.proximity_pressure_timer = max(0.0, self.proximity_pressure_timer - dt * 1.8)

    def _try_trigger_shockwave(self):
        if not self.cooldown_ready("shockwave"):
            return False
        if self.proximity_pressure_timer < self.shockwave_trigger_time:
            return False
        self.proximity_pressure_timer = 0.0
        self.shockwave_damage_done = False
        self.shockwave_committed = True
        self.set_action("shockwave_windup", self.shockwave_windup_duration)
        return True

    def _try_start_attack(self, distance_to_player):
        if distance_to_player <= self.melee_range and self.cooldown_ready("melee"):
            self.set_action("melee_windup", 0.22)
            self.melee_damage_done = False
            return True
        if distance_to_player <= self.shockwave_trigger_radius and self.cooldown_ready("shockwave"):
            return False
        if 88 <= distance_to_player <= self.charge_range and self.cooldown_ready("charge"):
            self.set_action("charge_windup", 0.72)
            return True
        if self.phase >= 2 and distance_to_player >= 110 and self.cooldown_ready("spikes"):
            self.set_action("spike_windup", 0.5)
            return True
        return False

    def _update_movement_brain(self, dt, game_scene, player_center, distance_to_player):
        self.strafe_swap_timer = max(0.0, self.strafe_swap_timer - dt)
        if self.strafe_swap_timer == 0.0:
            self.strafe_clockwise = not self.strafe_clockwise
            self.strafe_swap_timer = random.uniform(1.0, 2.1)

        if distance_to_player > 185:
            self.set_action("approach", 0.4)
            self._move_towards(player_center.x, player_center.y, dt, game_scene, speed=self.speed * 1.02, use_pathfinding=True)
            return
        if distance_to_player < 72:
            self.set_action("retreat", 0.25)
            self.move_evade(player_center.x, player_center.y, dt, game_scene, speed_scale=1.0)
            return
        desired_distance = 150 if self.phase >= 2 else 120
        self.set_action("orbit", 0.5)
        self.move_orbit(player_center.x, player_center.y, dt, game_scene, desired_distance=desired_distance, speed_scale=0.95)

    def _update_melee_windup(self, dt, game_scene, player):
        player_center = player.get_center()
        direction = self.face_towards(player_center)
        if direction.length() > 0:
            direction = direction.normalize()
            self._move_with_collision(direction.x * self.speed * 0.22 * dt, direction.y * self.speed * 0.22 * dt, game_scene)
        if self.action_timer > 0.0:
            return
        self.activate_attack_hitbox(0.12)
        if not self.melee_damage_done and self._boss_attack_hits_player(player):
            player.take_damage(self.damage)
            self.melee_damage_done = True
        self.deactivate_attack_hitbox()
        self.set_cooldown("melee", 1.35)
        self.set_action("recover", 0.34)

    def _update_charge_windup(self, dt, game_scene, player):
        player_center = player.get_center()
        direction = self.face_towards(player_center)
        if direction.length() > 0:
            self.charge_direction = direction.normalize()
        self.move_orbit(player_center.x, player_center.y, dt, game_scene, desired_distance=145, speed_scale=0.3)
        if self.action_timer > 0.0:
            return
        self.charge_time_left = self.charge_duration
        self.charge_hit_player = False
        self.activate_attack_hitbox(self.charge_duration)
        self.set_action("charge", self.charge_duration)

    def _update_charge(self, dt, game_scene, player):
        self.charge_time_left = max(0.0, self.charge_time_left - dt)
        move_x = self.charge_direction.x * self.charge_speed * self.charge_speed_multiplier * dt
        move_y = self.charge_direction.y * self.charge_speed * self.charge_speed_multiplier * dt
        moved = self._move_with_collision(move_x, move_y, game_scene)
        self._update_facing_from_direction(self.charge_direction)
        if not self.charge_hit_player and self._boss_attack_hits_player(player):
            player.take_damage(int(self.damage * 1.5))
            self.charge_hit_player = True
            self.charge_time_left = 0.0
        if self.action_timer > 0.0 and moved and self.charge_time_left > 0.0:
            return
        self.deactivate_attack_hitbox()
        self.set_cooldown("charge", 3.2)
        self.set_action("recover", 0.52)

    def _update_shockwave_windup(self, dt, game_scene, player):
        player_center = player.get_center()
        self.face_towards(player_center)
        if self.action_timer > 0.0:
            return
        self.set_action("shockwave_burst", self.shockwave_burst_duration)

    def _update_shockwave_burst(self, dt, game_scene, player):
        if not self.shockwave_damage_done:
            boss_center = self.get_center()
            player_center = player.get_center()
            to_player = Vector2(player_center.x - boss_center.x, player_center.y - boss_center.y)
            if to_player.length() <= self.shockwave_radius:
                if to_player.length() == 0:
                    to_player = Vector2(-1 if self.facing_left else 1, 0)
                player.take_damage(
                    int(self.damage * 1.25),
                    direction=to_player.normalize(),
                    force=2300.0,
                    stun_duration=0.65,
                )
            self.shockwave_damage_done = True
            self.set_cooldown("shockwave", 4.8)
        if self.action_timer > 0.0:
            return
        self.shockwave_committed = False
        self.set_action("recover", 0.36)

    def _update_spike_windup(self, dt, game_scene, player):
        player_center = player.get_center()
        self.face_towards(player_center)
        self.move_orbit(player_center.x, player_center.y, dt, game_scene, desired_distance=175, speed_scale=0.42)
        if self.action_timer > 0.0:
            return
        self.volley_shots_remaining = 3
        self.volley_burst_timer = 0.0
        self.set_action("spike_volley", 0.9)

    def _update_spike_volley(self, dt, game_scene, player):
        player_center = player.get_center()
        self.face_towards(player_center)
        self.move_orbit(player_center.x, player_center.y, dt, game_scene, desired_distance=185, speed_scale=0.36)
        self.volley_burst_timer -= dt
        if self.volley_shots_remaining > 0 and self.volley_burst_timer <= 0.0:
            self._fire_spike_burst(player_center)
            self.volley_shots_remaining -= 1
            self.volley_burst_timer = 0.26
        if self.volley_shots_remaining > 0:
            return
        if self.volley_burst_timer > 0.0:
            return
        self.set_cooldown("spikes", 4.4)
        self.set_action("recover", 0.4)

    def _update_recover(self, dt, game_scene, player):
        player_center = player.get_center()
        self.face_towards(player_center)
        if self.phase >= 2:
            self.move_orbit(player_center.x, player_center.y, dt, game_scene, desired_distance=160, speed_scale=0.52)
        else:
            self.move_evade(player_center.x, player_center.y, dt, game_scene, speed_scale=0.65)
        if self.action_timer == 0.0:
            self.set_action("orbit", 0.3)

    def _fire_spike_burst(self, player_center):
        origin = self.get_center()
        direction = Vector2(player_center.x - origin.x, player_center.y - origin.y)
        if direction.length() == 0:
            direction = Vector2(-1 if self.facing_left else 1, 0)
        direction = direction.normalize()
        for angle_degrees in (0.0, -self.volley_spread_degrees, self.volley_spread_degrees):
            projectile_direction = self._rotate(direction, math.radians(angle_degrees))
            self.projectiles.append(
                SpikeProjectile(
                    origin.x + projectile_direction.x * 18,
                    origin.y + projectile_direction.y * 18,
                    projectile_direction.x,
                    projectile_direction.y,
                    speed=280,
                    damage=max(4, int(self.damage * 0.7)),
                    radius=6,
                )
            )

    def _rotate(self, direction, angle):
        return Vector2(
            direction.x * math.cos(angle) - direction.y * math.sin(angle),
            direction.x * math.sin(angle) + direction.y * math.cos(angle),
        ).normalize()

    def _boss_attack_hits_player(self, player):
        attack_rect = self.get_attack_hitbox_at(self.position.x, self.position.y)
        if attack_rect is None:
            return False
        return rects_intersect(attack_rect, player.get_hitbox_rect())

    def _update_projectiles(self, dt, game_scene):
        alive_projectiles = []
        for projectile in self.projectiles:
            projectile.update(dt, game_scene)
            if not projectile.is_dead:
                alive_projectiles.append(projectile)
        self.projectiles = alive_projectiles

    def _load_sprite_animations(self):
        animations = {}
        frame_width, frame_height = self.SPRITE_FRAME_SIZE
        target_size = self._get_sprite_target_size()
        for name, (filename, frame_count, frame_duration) in self.SPRITE_ASSETS.items():
            path = self.sprite_asset_dir / filename
            frames = self._load_animation_frames(path, frame_count, frame_width, frame_height, target_size)
            animations[name] = {
                "frames": frames,
                "frame_duration": frame_duration,
            }
        return animations

    def _load_animation_frames(self, path, frame_count, frame_width, frame_height, target_size):
        sheet = load_image(path)
        if sheet is None:
            return []
        frames = []
        for index in range(frame_count):
            source_rect = pygame.Rect(index * frame_width, 0, frame_width, frame_height)
            if source_rect.right > sheet.get_width() or source_rect.bottom > sheet.get_height():
                break
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), source_rect)
            if target_size != (frame_width, frame_height):
                frame = pygame.transform.scale(frame, target_size)
            frames.append(frame)
        return frames

    def _resolve_animation_name(self, moved):
        if self.action_state in {"charge_windup", "charge"}:
            return "charge"
        if self.action_state in {"melee_windup", "shockwave_windup", "shockwave_burst"}:
            return "melee"
        if moved or self.action_state in {"approach", "retreat", "orbit", "evade", "recover", "phase_shift", "spike_windup", "spike_volley"}:
            return "move"
        return "idle"

    def _get_animation_frame(self, animation_name, frame_index):
        animation = self.sprite_animations.get(animation_name, {})
        frames = animation.get("frames", [])
        if frames:
            return frames[frame_index % len(frames)]
        fallback = self.sprite_animations.get("idle", {})
        fallback_frames = fallback.get("frames", [])
        if fallback_frames:
            return fallback_frames[0]
        return None

    def _update_animation(self, dt, moved):
        animation_name = self._resolve_animation_name(moved)
        animation = self.sprite_animations.get(animation_name, {})
        frames = animation.get("frames", [])
        if not frames:
            self.current_animation = animation_name
            self.current_frame_index = 0
            self.current_sprite = self._get_animation_frame(animation_name, 0)
            return
        if self.current_animation != animation_name:
            self.current_animation = animation_name
            self.current_frame_index = 0
            self.animation_frame_timer = 0.0
        frame_duration = max(0.01, float(animation.get("frame_duration", 0.12)))
        if len(frames) > 1:
            self.animation_frame_timer += dt
            while self.animation_frame_timer >= frame_duration:
                self.animation_frame_timer -= frame_duration
                self.current_frame_index = (self.current_frame_index + 1) % len(frames)
        else:
            self.current_frame_index = 0
            self.animation_frame_timer = 0.0
        self.current_sprite = frames[self.current_frame_index]

    def _draw_body(self, screen, camera):
        x = self.position.x - camera.position.x
        y = self.position.y - camera.position.y
        sprite = self.current_sprite
        if sprite is None:
            self._draw_fallback_body(screen, camera)
            return
        native_facing_left = self.SPRITE_NATIVE_FACING_LEFT.get(self.current_animation, False)
        if self.facing_left != native_facing_left:
            sprite = pygame.transform.flip(sprite, True, False)
        if self.phase >= 2:
            sprite = sprite.copy()
            sprite.fill((20, 45, 70, 0), special_flags=pygame.BLEND_RGB_ADD)
        if self.hurt_flash_timer > 0:
            sprite = sprite.copy()
            sprite.fill((100, 100, 100, 0), special_flags=pygame.BLEND_RGB_ADD)
        self._blit_body_sprite(screen, camera, sprite)

        if self.phase_glow_timer > 0:
            alpha = int(90 * min(1.0, self.phase_glow_timer / 1.2))
            glow = pygame.Surface((int(self.width + 32), int(self.height + 28)), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (120, 210, 255, alpha), glow.get_rect(), width=4)
            screen.blit(glow, (x - 16, y - 10))

    def _draw_fallback_body(self, screen, camera):
        x = self.position.x - camera.position.x
        y = self.position.y - camera.position.y
        flash = self.hurt_flash_timer > 0
        phase_tint = (110, 170, 210) if self.phase >= 2 else (148, 104, 62)
        body_color = (245, 245, 245) if flash else phase_tint
        accent_color = (232, 224, 205) if flash else (214, 188, 150)
        head_offset = -12 if self.facing_left else 12
        body_rect = pygame.Rect(int(x + 10), int(y + 20), int(self.width - 20), 26)
        head_center = (int(x + self.width / 2 + head_offset), int(y + 21))

        pygame.draw.ellipse(screen, body_color, body_rect)
        pygame.draw.ellipse(screen, COLORS["BLACK"], body_rect, width=2)
        pygame.draw.circle(screen, accent_color, head_center, 11)
        pygame.draw.circle(screen, COLORS["BLACK"], head_center, 11, width=2)

        antler_dir = -1 if self.facing_left else 1
        antler_base_x = head_center[0] + antler_dir * 3
        antler_color = (228, 244, 255) if self.phase >= 2 else (225, 213, 180)
        pygame.draw.line(screen, antler_color, (antler_base_x, head_center[1] - 8), (antler_base_x + antler_dir * 10, head_center[1] - 24), 3)
        pygame.draw.line(screen, antler_color, (antler_base_x, head_center[1] - 6), (antler_base_x + antler_dir * 14, head_center[1] - 14), 3)
        pygame.draw.line(screen, antler_color, (antler_base_x, head_center[1] - 10), (antler_base_x + antler_dir * 4, head_center[1] - 24), 3)

        for leg_x in (x + 18, x + 30, x + 46, x + 58):
            pygame.draw.rect(screen, body_color, (leg_x, y + 38, 6, 18), border_radius=3)
            pygame.draw.rect(screen, COLORS["BLACK"], (leg_x, y + 38, 6, 18), width=1, border_radius=3)
        pygame.draw.circle(screen, COLORS["BLACK"], (head_center[0] + antler_dir * 3, head_center[1] - 2), 2)

    def _draw_charge_telegraph(self, screen, camera):
        if self.action_state != "charge_windup":
            return
        center = self.get_center()
        start = (int(center.x - camera.position.x), int(center.y - camera.position.y))
        end = (
            int(center.x + self.charge_direction.x * 240 - camera.position.x),
            int(center.y + self.charge_direction.y * 240 - camera.position.y),
        )
        pygame.draw.line(screen, (255, 120, 90), start, end, width=4)
        pygame.draw.circle(screen, (255, 190, 150), end, 10, width=2)

    def _draw_spike_telegraph(self, screen, camera):
        if self.action_state != "spike_windup":
            return
        center = self.get_center()
        radius = 24 + int((0.5 - self.action_timer) * 22)
        pygame.draw.circle(
            screen,
            (150, 220, 255),
            (int(center.x - camera.position.x), int(center.y - camera.position.y)),
            max(18, radius),
            width=2,
        )

    def _draw_proximity_ring(self, screen, camera):
        if not SHOW_ENEMY_ATTACK_RADII:
            return
        center = self.get_center()
        screen_center = (int(center.x - camera.position.x), int(center.y - camera.position.y))
        base_radius = int(self.shockwave_trigger_radius)
        progress = max(0.0, min(1.0, self.proximity_pressure_timer / max(0.001, self.shockwave_trigger_time)))

        ring_surface_size = (base_radius + 12) * 2
        ring_surface = pygame.Surface((ring_surface_size, ring_surface_size), pygame.SRCALPHA)
        ring_rect = ring_surface.get_rect(center=screen_center)
        local_center = (ring_rect.width // 2, ring_rect.height // 2)

        fill_alpha = int(18 + 42 * progress)
        border_alpha = int(70 + 120 * progress)
        fill_color = (90, 210, 255, fill_alpha)
        border_color = (140, 235, 255, border_alpha)
        pulse_radius = max(8, int(base_radius * progress))

        pygame.draw.circle(ring_surface, fill_color, local_center, pulse_radius)
        pygame.draw.circle(ring_surface, border_color, local_center, base_radius, width=2)

        if progress > 0:
            warning_alpha = int(80 * progress)
            pygame.draw.circle(
                ring_surface,
                (255, 240, 190, warning_alpha),
                local_center,
                max(base_radius - 2, 2),
                width=3,
            )

        screen.blit(ring_surface, ring_rect.topleft)

    def _draw_shockwave_telegraph(self, screen, camera):
        if self.action_state not in {"shockwave_windup", "shockwave_burst"}:
            return
        center = self.get_center()
        progress = 1.0
        if self.action_state == "shockwave_windup":
            progress = 1.0 - (
                self.action_timer / self.shockwave_windup_duration if self.shockwave_windup_duration > 0 else 0.0
            )
        radius = int(28 + (self.shockwave_radius - 28) * max(0.0, min(1.0, progress)))
        width = 3 if self.action_state == "shockwave_windup" else 5
        color = (160, 235, 255) if self.action_state == "shockwave_windup" else (210, 245, 255)
        pygame.draw.circle(
            screen,
            color,
            (int(center.x - camera.position.x), int(center.y - camera.position.y)),
            radius,
            width=width,
        )

    def draw(self, screen, camera):
        if self.is_dead:
            return
        for projectile in self.projectiles:
            projectile.draw(screen, camera)
        self._draw_proximity_ring(screen, camera)
        self._draw_charge_telegraph(screen, camera)
        self._draw_spike_telegraph(screen, camera)
        self._draw_shockwave_telegraph(screen, camera)
        self._draw_body(screen, camera)
        self._draw_health_bar(screen, camera)
        if SHOW_INTERACTION_ZONES:
            self.draw_debug(screen, camera)
