from __future__ import annotations

import math
import random
from collections import deque

import pygame

from game.core.assets import load_image
from game.core.timer import Timer
from game.core.vector import Vector2
from game.entities.enemies.ai.behaviors import can_detect_player, pick_patrol_target, start_chase
from game.entities.enemies.ai.states import CHASE, INVESTIGATE, LINGER, PATROL_IDLE, PATROL_MOVE, RETURN_HOME
from game.entities.enemies.ai.steering import point_distance
from game.entities.entity import Entity
from settings import ASSETS_DIR, COLORS, SHOW_ENEMY_ATTACK_RADII, SHOW_INTERACTION_ZONES


class Enemy(Entity):
    SPRITE_FRAME_SIZE = None
    SPRITE_FRAME_DURATIONS = {}
    SPRITE_NATIVE_FACING_LEFT = {}
    SPRITE_ANIMATIONS = {}
    HIDDEN_REVEAL_RADIUS = 42.0
    DEATH_SPRITE_FRAME_SIZE = (64, 64)
    DEATH_SPRITE_FRAME_COUNT = 5
    DEATH_SPRITE_FRAME_DURATION = 0.08
    DEATH_SPRITE_PATH = ASSETS_DIR / "enemies" / "death_sprite" / "base_death_entities.png"
    BODY_HITBOX = None
    HURTBOX = None
    ATTACK_HITBOX = None
    COLLISION_CIRCLE = None
    LOOT_TABLE = ()
    BASE_RESISTANCES = {
        "melee": 0.0,
        "ranged": 0.0,
        "fire": 0.0,
        "cold": 0.0,
        "slow": 0.0,
        "poison": 0.0,
    }

    def __init__(
        self,
        x,
        y,
        width,
        height,
        hitbox_width=None,
        hitbox_height=None,
        hitbox_offset_x=None,
        hitbox_offset_y=None,
        name="enemy",
        max_health=20,
        speed=80,
        damage=4,
        attack_cooldown=1.0,
        detection_radius=160,
        patrol_radius=140,
        patrol_idle_min=0.45,
        patrol_idle_max=1.1,
        linger_duration=1.0,
        color=None,
        xp_reward=10,
        hurtbox_width=None,
        hurtbox_height=None,
        hurtbox_offset_x=None,
        hurtbox_offset_y=None,
        attack_hitbox_width=None,
        attack_hitbox_height=None,
        attack_hitbox_offset_x=None,
        attack_hitbox_offset_y=None,
        attack_hitbox_mirror_with_facing=None,
        resistances=None,
        scale=1.0,
    ):
        self.scale = max(0.1, float(scale))
        width = max(1, int(round(float(width) * self.scale)))
        height = max(1, int(round(float(height) * self.scale)))
        hitbox_size = int(min(width, height) * 0.66)
        body_hitbox = dict(self.BODY_HITBOX or {})
        hurtbox = dict(self.HURTBOX or {})
        attack_hitbox = dict(self.ATTACK_HITBOX or {})
        collision_circle = dict(self.COLLISION_CIRCLE or {})

        def scaled_value(value):
            return float(value) * self.scale

        resolved_hitbox_width = (
            scaled_value(hitbox_width)
            if hitbox_width is not None
            else scaled_value(body_hitbox.get("width", hitbox_size))
        )
        resolved_hitbox_height = (
            scaled_value(hitbox_height)
            if hitbox_height is not None
            else scaled_value(body_hitbox.get("height", hitbox_size))
        )
        resolved_hitbox_offset_x = (
            scaled_value(hitbox_offset_x)
            if hitbox_offset_x is not None
            else scaled_value(body_hitbox.get("offset_x", (width / self.scale - resolved_hitbox_width / self.scale) / 2))
        )
        resolved_hitbox_offset_y = (
            scaled_value(hitbox_offset_y)
            if hitbox_offset_y is not None
            else scaled_value(body_hitbox.get("offset_y", (height / self.scale - resolved_hitbox_height / self.scale) / 2))
        )
        super().__init__(
            x,
            y,
            width,
            height,
            hitbox_width=resolved_hitbox_width,
            hitbox_height=resolved_hitbox_height,
            hitbox_offset_x=resolved_hitbox_offset_x,
            hitbox_offset_y=resolved_hitbox_offset_y,
            collision_circle_radius=float(
                scaled_value(collision_circle.get("radius", min(resolved_hitbox_width, resolved_hitbox_height) / 2 / self.scale))
            ),
            collision_circle_offset_x=float(
                scaled_value(collision_circle.get("offset_x", (resolved_hitbox_offset_x + resolved_hitbox_width / 2) / self.scale))
            ),
            collision_circle_offset_y=float(
                scaled_value(collision_circle.get("offset_y", (resolved_hitbox_offset_y + resolved_hitbox_height / 2) / self.scale))
            ),
        )
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
        self.xp_reward = max(0, int(xp_reward))
        self.xp_awarded = False
        self.hurtbox_width = (
            scaled_value(hurtbox_width)
            if hurtbox_width is not None
            else scaled_value(hurtbox.get("width", self.hitbox_width / self.scale))
        )
        self.hurtbox_height = (
            scaled_value(hurtbox_height)
            if hurtbox_height is not None
            else scaled_value(hurtbox.get("height", self.hitbox_height / self.scale))
        )
        self.hurtbox_offset_x = (
            scaled_value(hurtbox_offset_x)
            if hurtbox_offset_x is not None
            else scaled_value(hurtbox.get("offset_x", self.hitbox_offset_x / self.scale))
        )
        self.hurtbox_offset_y = (
            scaled_value(hurtbox_offset_y)
            if hurtbox_offset_y is not None
            else scaled_value(hurtbox.get("offset_y", self.hitbox_offset_y / self.scale))
        )
        self.attack_hitbox_width = (
            scaled_value(attack_hitbox_width)
            if attack_hitbox_width is not None
            else (scaled_value(attack_hitbox["width"]) if "width" in attack_hitbox else None)
        )
        self.attack_hitbox_height = (
            scaled_value(attack_hitbox_height)
            if attack_hitbox_height is not None
            else (scaled_value(attack_hitbox["height"]) if "height" in attack_hitbox else None)
        )
        self.attack_hitbox_offset_x = (
            scaled_value(attack_hitbox_offset_x)
            if attack_hitbox_offset_x is not None
            else scaled_value(attack_hitbox.get("offset_x", 0))
        )
        self.attack_hitbox_offset_y = (
            scaled_value(attack_hitbox_offset_y)
            if attack_hitbox_offset_y is not None
            else scaled_value(attack_hitbox.get("offset_y", 0))
        )
        self.attack_hitbox_mirror_with_facing = (
            bool(attack_hitbox_mirror_with_facing)
            if attack_hitbox_mirror_with_facing is not None
            else bool(attack_hitbox.get("mirror_with_facing", True))
        )
        self.attack_hitbox_active = False
        self.attack_hitbox_timer = Timer(0.0)
        self.loot_table = [dict(entry) for entry in self.LOOT_TABLE]
        self.resistances = self._build_resistances(resistances)
        self.last_damage_taken = 0
        self.death_animation_frames = self._load_death_animation_frames()
        self.death_animation_frame_index = 0
        self.death_animation_timer = 0.0
        self.death_animation_finished = False
        self.ready_for_removal = False
        self.home_position = Vector2(x, y)
        self.patrol_radius = max(self.width, int(patrol_radius))
        self.patrol_idle_min = max(0.0, float(patrol_idle_min))
        self.patrol_idle_max = max(self.patrol_idle_min, float(patrol_idle_max))
        self.linger_duration = max(0.0, float(linger_duration))
        self.behavior_state = PATROL_MOVE
        self.patrol_target = pick_patrol_target(self)
        self.patrol_idle_timer = 0.0
        self.patrol_turn_timer = random.uniform(0.25, 0.75)
        self.linger_timer = 0.0
        self.last_chase_direction = Vector2(0, 0)
        self.patrol_speed = max(20, int(self.speed * 0.6))
        self.return_speed = max(20, int(self.speed * 0.85))
        self.path_recalc_interval = 0.35
        self.path_recalc_timer = 0.0
        self.current_path = []
        self.current_path_target_tile = None
        self.stuck_timer = 0.0
        self.stuck_timeout = 3.0
        self.stuck_repath_cooldown = 0.0
        self.hurt_flash_timer = 0.0
        self.stun_timer = 0.0
        self.knockback_velocity = Vector2(0, 0)
        self.background_update_accumulator = 0.0
        self.encounter_started = False
        self.investigate_target = None
        self.investigate_wait_duration = 1.0
        self.investigate_wait_timer = 0.0
        self.sprite_animations = {}
        self.current_animation = "idle"
        self.current_frame_index = 0
        self.animation_frame_timer = 0.0
        self.current_sprite = None
        self._initialize_sprite_animations()

    def _build_resistances(self, overrides=None):
        resistances = dict(self.BASE_RESISTANCES)
        for key, value in (overrides or {}).items():
            normalized_key = str(key).strip().lower()
            if normalized_key not in resistances:
                continue
            resistances[normalized_key] = min(1.0, max(0.0, float(value)))
        return resistances

    def get_resistance(self, resistance_type):
        normalized_type = str(resistance_type).strip().lower()
        return float(self.resistances.get(normalized_type, 0.0))

    def get_effect_value_after_resistance(self, resistance_type, value):
        return float(value) * max(0.0, 1.0 - self.get_resistance(resistance_type))

    def _resolve_damage_resistance_type(self, attack_kind):
        if attack_kind is None:
            return None
        normalized_kind = str(attack_kind).strip().lower()
        if normalized_kind in {"light", "heavy", "charged", "melee"}:
            return "melee"
        if normalized_kind in {"ranged", "fire", "cold", "poison"}:
            return normalized_kind
        return None

    def _apply_damage_resistance(self, damage, attack_kind=None):
        amount = max(1, int(damage))
        resistance_type = self._resolve_damage_resistance_type(attack_kind)
        if resistance_type is None:
            return amount
        resistance = self.get_resistance(resistance_type)
        mitigated = int(round(amount * (1.0 - resistance)))
        return max(0, mitigated)

    def take_damage(self, damage, attack_kind=None):
        amount = self._apply_damage_resistance(damage, attack_kind=attack_kind)
        self.last_damage_taken = amount
        if amount <= 0:
            return False
        self.health = max(0, self.health - amount)
        self.hurt_flash_timer = 0.12
        if self.health <= 0:
            self.is_dead = True
            self.attack_hitbox_active = False
            self.death_animation_frame_index = 0
            self.death_animation_timer = 0.0
            self.death_animation_finished = False
            self.ready_for_removal = False
        return True

    def _load_death_animation_frames(self):
        sheet = load_image(self.DEATH_SPRITE_PATH)
        if sheet is None:
            return []
        frame_width, frame_height = self.DEATH_SPRITE_FRAME_SIZE
        target_size = (int(self.width), int(self.height))
        frames = []
        for index in range(self.DEATH_SPRITE_FRAME_COUNT):
            source_rect = pygame.Rect(index * frame_width, 0, frame_width, frame_height)
            if source_rect.right > sheet.get_width() or source_rect.bottom > sheet.get_height():
                break
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), source_rect)
            if target_size != (frame_width, frame_height):
                frame = pygame.transform.scale(frame, target_size)
            frames.append(frame)
        return frames

    def update_death_animation(self, dt):
        if self.death_animation_finished:
            self.ready_for_removal = True
            return
        if not self.death_animation_frames:
            self.death_animation_finished = True
            self.ready_for_removal = True
            return
        if self.death_animation_frame_index >= len(self.death_animation_frames) - 1:
            self.death_animation_finished = True
            self.ready_for_removal = True
            return
        self.death_animation_timer += dt
        while self.death_animation_timer >= self.DEATH_SPRITE_FRAME_DURATION:
            self.death_animation_timer -= self.DEATH_SPRITE_FRAME_DURATION
            self.death_animation_frame_index += 1
            if self.death_animation_frame_index >= len(self.death_animation_frames) - 1:
                self.death_animation_frame_index = len(self.death_animation_frames) - 1
                self.death_animation_finished = True
                self.ready_for_removal = True
                break

    def draw_death(self, screen, camera):
        if not self.death_animation_frames:
            return
        frame = self.death_animation_frames[min(self.death_animation_frame_index, len(self.death_animation_frames) - 1)]
        screen.blit(frame, (self.position.x - camera.position.x, self.position.y - camera.position.y))

    def apply_hit_reaction(self, direction, force=0.0, stun=0.0):
        if direction.length() > 0 and force > 0:
            self.knockback_velocity = direction.normalize() * force
        self.stun_timer = max(self.stun_timer, stun)
        self.current_path = []
        self.current_path_target_tile = None

    def alert_to_position(self, world_x, world_y):
        if self.is_dead:
            return
        self.encounter_started = True
        self.investigate_target = Vector2(float(world_x), float(world_y))
        self.investigate_wait_timer = self.investigate_wait_duration
        self.current_path = []
        self.current_path_target_tile = None
        if self.behavior_state != CHASE:
            self.behavior_state = INVESTIGATE

    def update(self, dt, game_scene):
        if self.is_dead:
            return
        self.attack_cooldown.update(dt)
        if self.attack_hitbox_timer.update(dt):
            self.attack_hitbox_active = False
        self.stuck_repath_cooldown = max(0.0, self.stuck_repath_cooldown - dt)
        self.hurt_flash_timer = max(0.0, self.hurt_flash_timer - dt)

        if self._update_knockback(dt, game_scene):
            return
        if self.stun_timer > 0:
            self.stun_timer = max(0.0, self.stun_timer - dt)
            return

        player = game_scene.player
        player_center = player.get_center()
        distance_to_player = point_distance(self.get_center(), player_center)

        if can_detect_player(self, player, distance_to_player):
            start_chase(self, player_center)
            self.encounter_started = True
            self.investigate_target = None
            self.investigate_wait_timer = 0.0
            return
        if self.behavior_state == CHASE:
            self.behavior_state = LINGER
        if self.behavior_state == LINGER:
            self._update_linger(dt, game_scene)
            return
        if self.behavior_state == INVESTIGATE:
            self._update_investigate(dt, game_scene)
            return
        if self.behavior_state == RETURN_HOME:
            self._update_return_home(dt, game_scene)
            return
        if self.behavior_state == PATROL_IDLE:
            self._reset_stuck_state()
            self._update_patrol_idle(dt)
            return

        previous_position = Vector2(self.position.x, self.position.y)
        self._update_patrol_move(dt, game_scene)
        self._update_stuck_state(dt, previous_position, game_scene)

    def _update_linger(self, dt, game_scene):
        previous_position = Vector2(self.position.x, self.position.y)
        if self.linger_timer <= 0:
            self.behavior_state = RETURN_HOME
            return
        direction = self.last_chase_direction
        if direction.length() > 0:
            move_x = direction.x * self.speed * dt
            move_y = direction.y * self.speed * dt
            self._move_with_collision(move_x, move_y, game_scene)
            self._update_facing_from_direction(direction)
        self.linger_timer = max(0.0, self.linger_timer - dt)
        if self.linger_timer <= 0:
            self.behavior_state = RETURN_HOME
            self.current_path = []
            self.current_path_target_tile = None
        self._update_stuck_state(dt, previous_position, game_scene)

    def _update_return_home(self, dt, game_scene):
        home_center = self._home_center()
        if point_distance(self.get_center(), home_center) <= max(8.0, self.width * 0.25):
            self.behavior_state = PATROL_IDLE
            self.encounter_started = False
            self.investigate_target = None
            self.investigate_wait_timer = 0.0
            self.patrol_idle_timer = random.uniform(self.patrol_idle_min, self.patrol_idle_max)
            self.patrol_turn_timer = random.uniform(0.25, 0.75)
            self.patrol_target = pick_patrol_target(self)
            self._reset_stuck_state()
            return
        previous_position = Vector2(self.position.x, self.position.y)
        self._move_towards(home_center.x, home_center.y, dt, game_scene, speed=self.return_speed, use_pathfinding=True)
        self._update_stuck_state(dt, previous_position, game_scene)

    def _update_investigate(self, dt, game_scene):
        if self.investigate_target is None:
            self.behavior_state = RETURN_HOME
            return
        previous_position = Vector2(self.position.x, self.position.y)
        if point_distance(self.get_center(), self.investigate_target) <= max(10.0, self.width * 0.3):
            self.investigate_wait_timer = max(0.0, self.investigate_wait_timer - dt)
            if self.investigate_wait_timer <= 0:
                self.behavior_state = RETURN_HOME
                self.current_path = []
                self.current_path_target_tile = None
            self._reset_stuck_state()
            return
        self._move_towards(
            self.investigate_target.x,
            self.investigate_target.y,
            dt,
            game_scene,
            speed=self.return_speed,
            use_pathfinding=True,
        )
        self._update_stuck_state(dt, previous_position, game_scene)

    def _update_patrol_idle(self, dt):
        self.patrol_idle_timer = max(0.0, self.patrol_idle_timer - dt)
        self.patrol_turn_timer -= dt
        if self.patrol_turn_timer <= 0:
            self.facing_left = not self.facing_left
            self.patrol_turn_timer = random.uniform(0.25, 0.75)
        if self.patrol_idle_timer <= 0:
            self.patrol_target = pick_patrol_target(self)
            self.behavior_state = PATROL_MOVE
            self.current_path = []
            self.current_path_target_tile = None

    def _update_patrol_move(self, dt, game_scene):
        if self.patrol_target is None:
            self.patrol_target = pick_patrol_target(self)
        if point_distance(self.get_center(), self.patrol_target) <= max(6.0, self.width * 0.2):
            self.behavior_state = PATROL_IDLE
            self.patrol_idle_timer = random.uniform(self.patrol_idle_min, self.patrol_idle_max)
            self.patrol_turn_timer = random.uniform(0.25, 0.75)
            self._reset_stuck_state()
            return
        self._move_towards(self.patrol_target.x, self.patrol_target.y, dt, game_scene, speed=self.patrol_speed, use_pathfinding=True)

    def _home_center(self):
        return Vector2(self.home_position.x + self.width / 2, self.home_position.y + self.height / 2)

    def _move_towards(self, target_x, target_y, dt, game_scene, speed=None, use_pathfinding=False):
        speed = self.speed if speed is None else speed
        if use_pathfinding:
            waypoint = self._get_path_waypoint(target_x, target_y, dt, game_scene)
            if waypoint is not None:
                target_x = waypoint.x
                target_y = waypoint.y
        dx = target_x - self.get_center().x
        dy = target_y - self.get_center().y
        direction = Vector2(dx, dy)
        if direction.length() == 0:
            return
        direction = direction.normalize()
        self._move_with_collision(direction.x * speed * dt, direction.y * speed * dt, game_scene)
        self._update_facing_from_direction(direction)

    def _move_away_from(self, target_x, target_y, dt, game_scene, speed=None):
        speed = self.speed if speed is None else speed
        dx = self.get_center().x - target_x
        dy = self.get_center().y - target_y
        direction = Vector2(dx, dy)
        if direction.length() == 0:
            return
        direction = direction.normalize()
        self._move_with_collision(direction.x * speed * dt, direction.y * speed * dt, game_scene)
        self._update_facing_from_direction(direction)

    def _get_path_waypoint(self, target_x, target_y, dt, game_scene):
        self.path_recalc_timer = max(0.0, self.path_recalc_timer - dt)
        start_tile = self._world_to_tile(self.get_center().x, self.get_center().y, game_scene)
        target_tile = self._resolve_target_tile(target_x, target_y, game_scene)
        if target_tile is None or start_tile == target_tile:
            self.current_path = []
            self.current_path_target_tile = None
            return None
        if self.path_recalc_timer <= 0 or self.current_path_target_tile != target_tile or not self.current_path:
            self.current_path = self._build_path(start_tile, target_tile, game_scene)
            self.current_path_target_tile = target_tile
            self.path_recalc_timer = self.path_recalc_interval
        while self.current_path:
            waypoint_tile = self.current_path[0]
            waypoint = self._tile_to_world_center(*waypoint_tile, game_scene)
            if point_distance(self.get_center(), waypoint) <= max(6.0, self.width * 0.2):
                self.current_path.pop(0)
                continue
            return waypoint
        return None

    def _build_path(self, start_tile, target_tile, game_scene):
        queue = deque([start_tile])
        came_from = {start_tile: None}
        while queue:
            current = queue.popleft()
            if current == target_tile:
                break
            for neighbor in self._iter_path_neighbors(current, game_scene):
                if neighbor in came_from:
                    continue
                came_from[neighbor] = current
                queue.append(neighbor)
        if target_tile not in came_from:
            return []
        path = []
        current = target_tile
        while current is not None and current != start_tile:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def _iter_path_neighbors(self, tile, game_scene):
        tile_x, tile_y = tile
        for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            next_tile = (tile_x + offset_x, tile_y + offset_y)
            if self._can_occupy_tile(next_tile[0], next_tile[1], game_scene):
                yield next_tile

    def _resolve_target_tile(self, target_x, target_y, game_scene):
        base_tile = self._world_to_tile(target_x, target_y, game_scene)
        if self._can_occupy_tile(base_tile[0], base_tile[1], game_scene):
            return base_tile
        for radius in range(1, 4):
            for offset_x in range(-radius, radius + 1):
                for offset_y in range(-radius, radius + 1):
                    if abs(offset_x) + abs(offset_y) != radius:
                        continue
                    probe_tile = (base_tile[0] + offset_x, base_tile[1] + offset_y)
                    if self._can_occupy_tile(probe_tile[0], probe_tile[1], game_scene):
                        return probe_tile
        return None

    def _can_occupy_tile(self, tile_x, tile_y, game_scene):
        tile_size = game_scene.tilemap.tile_size
        return not game_scene.check_collision(tile_x * tile_size, tile_y * tile_size, self)

    def _world_to_tile(self, world_x, world_y, game_scene):
        tile_size = game_scene.tilemap.tile_size
        return int(world_x // tile_size), int(world_y // tile_size)

    def _tile_to_world_center(self, tile_x, tile_y, game_scene):
        tile_size = game_scene.tilemap.tile_size
        return Vector2(tile_x * tile_size + tile_size / 2, tile_y * tile_size + tile_size / 2)

    def _move_with_collision(self, move_x, move_y, game_scene):
        if move_x == 0 and move_y == 0:
            return False
        if self._try_move(move_x, move_y, game_scene):
            return True
        axis_attempts = []
        if move_x != 0:
            axis_attempts.append((move_x, 0))
        if move_y != 0:
            axis_attempts.append((0, move_y))
        for attempt_x, attempt_y in axis_attempts:
            if self._try_move(attempt_x, attempt_y, game_scene):
                return True
        step_length = math.sqrt(move_x * move_x + move_y * move_y)
        if step_length <= 0:
            return False
        direction = Vector2(move_x, move_y).normalize()
        lateral_candidates = [Vector2(-direction.y, direction.x), Vector2(direction.y, -direction.x)]
        for lateral in lateral_candidates:
            if self._try_move(lateral.x * step_length, lateral.y * step_length, game_scene):
                self._update_facing_from_direction(lateral)
                return True
        for lateral in lateral_candidates:
            blended = (direction + lateral * 0.85).normalize()
            if self._try_move(blended.x * step_length, blended.y * step_length, game_scene):
                self._update_facing_from_direction(blended)
                return True
        return False

    def _try_move(self, move_x, move_y, game_scene):
        moved = False
        if move_x != 0:
            new_x = self.position.x + move_x
            if not game_scene.check_collision(new_x, self.position.y, self):
                self.position.x = new_x
                moved = True
        if move_y != 0:
            new_y = self.position.y + move_y
            if not game_scene.check_collision(self.position.x, new_y, self):
                self.position.y = new_y
                moved = True
        return moved

    def _update_stuck_state(self, dt, previous_position, game_scene):
        moved_distance = point_distance(previous_position, self.position)
        if moved_distance > 1.0:
            self._reset_stuck_state()
            return
        if self.behavior_state not in {PATROL_MOVE, CHASE, LINGER, INVESTIGATE, RETURN_HOME}:
            self._reset_stuck_state()
            return
        self.stuck_timer += dt
        if self.stuck_timer < self.stuck_timeout or self.stuck_repath_cooldown > 0:
            return
        self._recover_from_stuck(game_scene)

    def _recover_from_stuck(self, game_scene):
        self.stuck_timer = 0.0
        self.stuck_repath_cooldown = 0.75
        self.current_path = []
        self.current_path_target_tile = None
        if self.behavior_state == PATROL_MOVE:
            self.patrol_target = pick_patrol_target(self)
            return
        if self.behavior_state == INVESTIGATE and self.investigate_target is not None:
            self.investigate_wait_timer = max(0.0, self.investigate_wait_timer - 0.2)
            return
        if self.behavior_state == LINGER and self.last_chase_direction.length() > 0:
            angle = random.choice((math.pi / 2, -math.pi / 2))
            direction = self.last_chase_direction
            rotated = Vector2(
                direction.x * math.cos(angle) - direction.y * math.sin(angle),
                direction.x * math.sin(angle) + direction.y * math.cos(angle),
            ).normalize()
            self.last_chase_direction = rotated
            return
        if self.behavior_state == CHASE:
            self._force_side_step(game_scene)

    def _force_side_step(self, game_scene):
        step = max(8.0, self.width * 0.35)
        directions = [Vector2(0, -1), Vector2(0, 1), Vector2(-1, 0), Vector2(1, 0)]
        random.shuffle(directions)
        for direction in directions:
            if self._try_move(direction.x * step, direction.y * step, game_scene):
                self._update_facing_from_direction(direction)
                break

    def _reset_stuck_state(self):
        self.stuck_timer = 0.0

    def _update_knockback(self, dt, game_scene):
        speed = self.knockback_velocity.length()
        if speed <= 0.01:
            self.knockback_velocity = Vector2(0, 0)
            return False
        step = self.knockback_velocity * dt
        self._try_move(step.x, step.y, game_scene)
        damping = max(0.0, 1.0 - dt * 8.0)
        self.knockback_velocity = self.knockback_velocity * damping
        return True

    def _update_facing_from_direction(self, direction):
        if abs(direction.x) > 0.0001:
            self.facing_left = direction.x < 0

    def _initialize_sprite_animations(self):
        if not self.SPRITE_ANIMATIONS or self.SPRITE_FRAME_SIZE is None:
            return
        animations = {}
        for animation_name, animation_entry in self.SPRITE_ANIMATIONS.items():
            path, frame_count = animation_entry
            resolved_path = path if hasattr(path, "exists") else ASSETS_DIR / str(path)
            animations[animation_name] = self._load_animation_frames(resolved_path, frame_count)
        self.sprite_animations = animations
        idle_frames = self.sprite_animations.get("idle", [])
        self.current_sprite = idle_frames[0] if idle_frames else None

    def _load_animation_frames(self, path, frame_count):
        sheet = load_image(path)
        if sheet is None or self.SPRITE_FRAME_SIZE is None:
            return []
        target_size = (int(self.width), int(self.height))
        frame_width, frame_height = self.SPRITE_FRAME_SIZE
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
        if moved:
            return "move"
        return "idle"

    def _update_animation(self, dt, moved):
        if not self.sprite_animations:
            self.current_sprite = None
            return
        animation_name = self._resolve_animation_name(moved)
        frames = self.sprite_animations.get(animation_name, [])
        if not frames:
            self.current_animation = animation_name
            self.current_frame_index = 0
            self.current_sprite = None
            return
        if self.current_animation != animation_name:
            self.current_animation = animation_name
            self.current_frame_index = 0
            self.animation_frame_timer = 0.0
        frame_duration = float(self.SPRITE_FRAME_DURATIONS.get(animation_name, 0.12))
        if len(frames) > 1:
            self.animation_frame_timer += dt
            while self.animation_frame_timer >= frame_duration:
                self.animation_frame_timer -= frame_duration
                self.current_frame_index = (self.current_frame_index + 1) % len(frames)
        else:
            self.current_frame_index = 0
            self.animation_frame_timer = 0.0
        self.current_sprite = frames[self.current_frame_index]

    def get_hurtbox_at(self, x, y):
        return (
            x + self.hurtbox_offset_x,
            y + self.hurtbox_offset_y,
            self.hurtbox_width,
            self.hurtbox_height,
        )

    def get_hurtbox_rect(self):
        return self.get_hurtbox_at(self.position.x, self.position.y)

    def has_attack_hitbox(self):
        return self.attack_hitbox_width is not None and self.attack_hitbox_height is not None

    def activate_attack_hitbox(self, duration=0.1):
        if not self.has_attack_hitbox():
            return False
        self.attack_hitbox_active = True
        if duration > 0:
            self.attack_hitbox_timer.duration = float(duration)
            self.attack_hitbox_timer.start(float(duration))
        return True

    def deactivate_attack_hitbox(self):
        self.attack_hitbox_active = False
        self.attack_hitbox_timer.active = False

    def roll_loot(self):
        rolled = []
        for raw_reward in self.loot_table:
            chance = float(raw_reward.get("chance", 1.0))
            if random.random() > chance:
                continue
            reward = dict(raw_reward)
            minimum = int(reward.get("min_quantity", reward.get("quantity", 1)))
            maximum = int(reward.get("max_quantity", reward.get("quantity", minimum)))
            minimum = max(1, minimum)
            maximum = max(minimum, maximum)
            reward["quantity"] = random.randint(minimum, maximum)
            rolled.append(reward)
        return rolled

    def get_attack_hitbox_at(self, x, y):
        if not self.has_attack_hitbox():
            return None
        offset_x = self.attack_hitbox_offset_x
        if self.attack_hitbox_mirror_with_facing and self.facing_left:
            offset_x = self.width - self.attack_hitbox_offset_x - self.attack_hitbox_width
        return (
            x + offset_x,
            y + self.attack_hitbox_offset_y,
            self.attack_hitbox_width,
            self.attack_hitbox_height,
        )

    def get_attack_hitbox_rect(self):
        if not self.attack_hitbox_active:
            return None
        return self.get_attack_hitbox_at(self.position.x, self.position.y)

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
        sprite = self.current_sprite
        if sprite is not None:
            native_facing_left = self.SPRITE_NATIVE_FACING_LEFT.get(self.current_animation, False)
            if self.facing_left != native_facing_left:
                sprite = pygame.transform.flip(sprite, True, False)
            if self.hurt_flash_timer > 0:
                sprite = sprite.copy()
                sprite.fill((100, 100, 100, 0), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(sprite, (self.position.x - camera.position.x, self.position.y - camera.position.y))
            return
        x = self.position.x - camera.position.x
        y = self.position.y - camera.position.y
        body_color = (255, 245, 245) if self.hurt_flash_timer > 0 else self.color
        pygame.draw.rect(screen, body_color, (x, y, self.width, self.height), border_radius=6)
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
        pygame.draw.rect(overlay, (*fill_color, alpha), overlay.get_rect(), border_radius=border_radius)
        pygame.draw.rect(overlay, border_color, overlay.get_rect(), width=border_width, border_radius=border_radius)
        screen.blit(overlay, rect.topleft)

    def _draw_rect_debug(self, screen, camera, rect, color, width=2):
        if rect is None:
            return
        x, y, w, h = rect
        pygame.draw.rect(
            screen,
            color,
            (x - camera.position.x, y - camera.position.y, w, h),
            width,
        )

    def _draw_detection_zone(self, screen, camera):
        if not SHOW_ENEMY_ATTACK_RADII:
            return
        self._draw_zone(screen, camera, self.detection_radius, (255, 80, 80), COLORS["INTERACTION_ZONE"], 28)

    def _draw_attack_zone(self, screen, camera):
        if not SHOW_ENEMY_ATTACK_RADII or self.attack_radius is None:
            return
        self._draw_zone(screen, camera, self.attack_radius, (255, 200, 80), (255, 220, 120), 22, border_width=2)

    def draw_debug(self, screen, camera):
        self._draw_detection_zone(screen, camera)
        self._draw_attack_zone(screen, camera)
        if SHOW_INTERACTION_ZONES:
            self._draw_rect_debug(screen, camera, self.get_hurtbox_rect(), (120, 220, 120), width=1)
            self._draw_rect_debug(screen, camera, self.get_attack_hitbox_rect(), (255, 180, 80), width=2)
        super().draw_debug(screen, camera)

    def draw(self, screen, camera):
        if self.is_dead:
            return
        self._draw_health_bar(screen, camera)
        self._draw_body(screen, camera)
        self.draw_debug(screen, camera)
