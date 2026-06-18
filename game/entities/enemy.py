from __future__ import annotations

import math
import random
from collections import deque

import pygame

from game.core.timer import Timer
from game.core.vector import Vector2
from game.entities.entity import Entity
from settings import COLORS, SHOW_INTERACTION_ZONES


class Enemy(Entity):
    HIDDEN_REVEAL_RADIUS = 42.0

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
        patrol_radius=140,
        patrol_idle_min=0.45,
        patrol_idle_max=1.1,
        linger_duration=1.0,
        color=None,
    ):
        hitbox_size = int(min(width, height) * 0.66)
        hitbox_offset_x = (width - hitbox_size) / 2
        hitbox_offset_y = (height - hitbox_size) / 2
        super().__init__(
            x,
            y,
            width,
            height,
            hitbox_width=hitbox_size,
            hitbox_height=hitbox_size,
            hitbox_offset_x=hitbox_offset_x,
            hitbox_offset_y=hitbox_offset_y,
            collision_circle_radius=hitbox_size / 2,
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

        self.home_position = Vector2(x, y)
        self.patrol_radius = max(self.width, int(patrol_radius))
        self.patrol_idle_min = max(0.0, float(patrol_idle_min))
        self.patrol_idle_max = max(self.patrol_idle_min, float(patrol_idle_max))
        self.linger_duration = max(0.0, float(linger_duration))

        self.behavior_state = "patrol_move"
        self.patrol_target = self._pick_patrol_target()
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
        self.stuck_repath_cooldown = max(0.0, self.stuck_repath_cooldown - dt)

        player = game_scene.player
        player_center = player.get_center()
        distance_to_player = _point_distance(self.get_center(), player_center)

        if self._can_detect_player(player, distance_to_player):
            self._start_chase(player_center)
            return

        if self.behavior_state == "chase":
            self.behavior_state = "linger"

        if self.behavior_state == "linger":
            self._update_linger(dt, game_scene)
            return

        if self.behavior_state == "return_home":
            self._update_return_home(dt, game_scene)
            return

        if self.behavior_state == "patrol_idle":
            self._reset_stuck_state()
            self._update_patrol_idle(dt)
            return

        previous_position = Vector2(self.position.x, self.position.y)
        self._update_patrol_move(dt, game_scene)
        self._update_stuck_state(dt, previous_position, game_scene)

    def _can_detect_player(self, player, distance_to_player):
        if distance_to_player > self.detection_radius:
            return False
        if not getattr(player, "is_hidden", False):
            return True
        return distance_to_player <= self.HIDDEN_REVEAL_RADIUS

    def _start_chase(self, player_center):
        direction = Vector2(player_center.x - self.get_center().x, player_center.y - self.get_center().y)
        if direction.length() > 0:
            self.last_chase_direction = direction.normalize()
        self.behavior_state = "chase"
        self.linger_timer = self.linger_duration
        self.path_recalc_timer = 0.0

    def _update_linger(self, dt, game_scene):
        previous_position = Vector2(self.position.x, self.position.y)
        if self.linger_timer <= 0:
            self.behavior_state = "return_home"
            return

        direction = self.last_chase_direction
        if direction.length() > 0:
            move_x = direction.x * self.speed * dt
            move_y = direction.y * self.speed * dt
            self._move_with_collision(move_x, move_y, game_scene)
            self._update_facing_from_direction(direction)

        self.linger_timer = max(0.0, self.linger_timer - dt)
        if self.linger_timer <= 0:
            self.behavior_state = "return_home"
            self.current_path = []
            self.current_path_target_tile = None
        self._update_stuck_state(dt, previous_position, game_scene)

    def _update_return_home(self, dt, game_scene):
        home_center = self._home_center()
        if _point_distance(self.get_center(), home_center) <= max(8.0, self.width * 0.25):
            self.behavior_state = "patrol_idle"
            self.patrol_idle_timer = random.uniform(self.patrol_idle_min, self.patrol_idle_max)
            self.patrol_turn_timer = random.uniform(0.25, 0.75)
            self.patrol_target = self._pick_patrol_target()
            self._reset_stuck_state()
            return

        previous_position = Vector2(self.position.x, self.position.y)
        self._move_towards(home_center.x, home_center.y, dt, game_scene, speed=self.return_speed, use_pathfinding=True)
        self._update_stuck_state(dt, previous_position, game_scene)

    def _update_patrol_idle(self, dt):
        self.patrol_idle_timer = max(0.0, self.patrol_idle_timer - dt)
        self.patrol_turn_timer -= dt
        if self.patrol_turn_timer <= 0:
            self.facing_left = not self.facing_left
            self.patrol_turn_timer = random.uniform(0.25, 0.75)

        if self.patrol_idle_timer <= 0:
            self.patrol_target = self._pick_patrol_target()
            self.behavior_state = "patrol_move"
            self.current_path = []
            self.current_path_target_tile = None

    def _update_patrol_move(self, dt, game_scene):
        if self.patrol_target is None:
            self.patrol_target = self._pick_patrol_target()

        if _point_distance(self.get_center(), self.patrol_target) <= max(6.0, self.width * 0.2):
            self.behavior_state = "patrol_idle"
            self.patrol_idle_timer = random.uniform(self.patrol_idle_min, self.patrol_idle_max)
            self.patrol_turn_timer = random.uniform(0.25, 0.75)
            self._reset_stuck_state()
            return

        self._move_towards(
            self.patrol_target.x,
            self.patrol_target.y,
            dt,
            game_scene,
            speed=self.patrol_speed,
            use_pathfinding=True,
        )

    def _home_center(self):
        return Vector2(self.home_position.x + self.width / 2, self.home_position.y + self.height / 2)

    def _pick_patrol_target(self):
        center = self._home_center()
        angle = random.uniform(0, math.tau)
        radius = random.uniform(self.width * 0.5, self.patrol_radius)
        return Vector2(
            center.x + math.cos(angle) * radius,
            center.y + math.sin(angle) * radius,
        )

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
        move_x = direction.x * speed * dt
        move_y = direction.y * speed * dt
        self._move_with_collision(move_x, move_y, game_scene)
        self._update_facing_from_direction(direction)

    def _move_away_from(self, target_x, target_y, dt, game_scene, speed=None):
        speed = self.speed if speed is None else speed
        dx = self.get_center().x - target_x
        dy = self.get_center().y - target_y
        direction = Vector2(dx, dy)
        if direction.length() == 0:
            return

        direction = direction.normalize()
        move_x = direction.x * speed * dt
        move_y = direction.y * speed * dt
        self._move_with_collision(move_x, move_y, game_scene)
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
            if _point_distance(self.get_center(), waypoint) <= max(6.0, self.width * 0.2):
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
        world_x = tile_x * tile_size
        world_y = tile_y * tile_size
        return not game_scene.check_collision(world_x, world_y, self)

    def _world_to_tile(self, world_x, world_y, game_scene):
        tile_size = game_scene.tilemap.tile_size
        return int(world_x // tile_size), int(world_y // tile_size)

    def _tile_to_world_center(self, tile_x, tile_y, game_scene):
        tile_size = game_scene.tilemap.tile_size
        return Vector2(
            tile_x * tile_size + tile_size / 2,
            tile_y * tile_size + tile_size / 2,
        )

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
        lateral_candidates = [
            Vector2(-direction.y, direction.x),
            Vector2(direction.y, -direction.x),
        ]

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
        moved_distance = _point_distance(previous_position, self.position)
        if moved_distance > 1.0:
            self._reset_stuck_state()
            return

        if self.behavior_state not in {"patrol_move", "chase", "linger", "return_home"}:
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

        if self.behavior_state == "patrol_move":
            self.patrol_target = self._pick_patrol_target()
            return

        if self.behavior_state == "linger" and self.last_chase_direction.length() > 0:
            angle = random.choice((math.pi / 2, -math.pi / 2))
            direction = self.last_chase_direction
            rotated = Vector2(
                direction.x * math.cos(angle) - direction.y * math.sin(angle),
                direction.x * math.sin(angle) + direction.y * math.cos(angle),
            ).normalize()
            self.last_chase_direction = rotated
            return

        if self.behavior_state == "chase":
            self._force_side_step(game_scene)

    def _force_side_step(self, game_scene):
        step = max(8.0, self.width * 0.35)
        directions = [
            Vector2(0, -1),
            Vector2(0, 1),
            Vector2(-1, 0),
            Vector2(1, 0),
        ]
        random.shuffle(directions)
        for direction in directions:
            if self._try_move(direction.x * step, direction.y * step, game_scene):
                self._update_facing_from_direction(direction)
                break

    def _reset_stuck_state(self):
        self.stuck_timer = 0.0

    def _update_facing_from_direction(self, direction):
        if abs(direction.x) > 0.0001:
            self.facing_left = direction.x < 0

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
        patrol_radius=140,
        patrol_idle_min=0.45,
        patrol_idle_max=1.1,
        linger_duration=1.0,
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
            color=(220, 55, 55),
        )
        self.melee_range = float(melee_range)
        self.attack_radius = self.melee_range

    def update(self, dt, game_scene):
        super().update(dt, game_scene)
        if self.is_dead:
            return

        if self.behavior_state != "chase":
            return

        player = game_scene.player
        player_center = player.get_center()
        distance = _point_distance(self.get_center(), player_center)

        if distance <= self.melee_range:
            if not self.attack_cooldown.is_active():
                player.take_damage(self.damage)
                self.attack_cooldown.start()
            return

        previous_position = Vector2(self.position.x, self.position.y)
        self._move_towards(player_center.x, player_center.y, dt, game_scene, use_pathfinding=True)
        self._update_stuck_state(dt, previous_position, game_scene)


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
        patrol_radius=160,
        patrol_idle_min=0.45,
        patrol_idle_max=1.1,
        linger_duration=1.0,
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

        if self.behavior_state != "chase":
            self._update_projectiles(dt, game_scene)
            return

        player = game_scene.player
        player_center = player.get_center()
        distance = _point_distance(self.get_center(), player_center)

        if distance > self.preferred_distance:
            previous_position = Vector2(self.position.x, self.position.y)
            self._move_towards(player_center.x, player_center.y, dt, game_scene, use_pathfinding=True)
            self._update_stuck_state(dt, previous_position, game_scene)
        elif distance < self.min_distance:
            previous_position = Vector2(self.position.x, self.position.y)
            self._move_away_from(player_center.x, player_center.y, dt, game_scene)
            self._update_stuck_state(dt, previous_position, game_scene)

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


def _point_distance(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy)


class _ProjectileProbe:
    def __init__(self, radius):
        self.radius = radius * 2

    def get_hitbox_at(self, x, y):
        return (x, y, self.radius, self.radius)
