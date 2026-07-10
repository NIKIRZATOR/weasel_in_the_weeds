from __future__ import annotations

import math

import pygame

from game.core.assets import load_image
from game.core.vector import Vector2
from game.entities.enemies.ai.states import CHASE
from game.entities.enemies.ai.steering import entity_distance
from game.entities.enemies.base import Enemy
from game.entities.enemies.projectiles import RangedProjectile
from game.effects import EffectType
from settings import ASSETS_DIR


class ArcherEnemy(Enemy):
    SPRITE_FRAME_SIZE = (64, 64)
    SPRITE_SHEET = "wasp_idle_moves.png"
    SPRITE_FRAME_DURATIONS = {
        "idle": 0.4,
        "move": 0.12,
        "attack": 0.09,
    }
    PROJECTILE_SPRITE = "attack_bullet.png"
    SPRITE_NATIVE_FACING_LEFT = False
    BODY_HITBOX = {
        "width": 40,
        "height": 40,
        "offset_x": 6,
        "offset_y": 11,
    }
    HURTBOX = {
        "width": 40,
        "height": 40,
        "offset_x": 7,
        "offset_y": 10,
    }
    ATTACK_HITBOX = {
        "width": 16,
        "height": 14,
        "offset_x": 18,
        "offset_y": 13,
        "mirror_with_facing": True,
    }
    COLLISION_CIRCLE = {
        "radius": 10,
    }
    LOOT_TABLE = (
        {"item_id": "feather", "min_quantity": 1, "max_quantity": 2, "chance": 0.7},
        {"item_id": "stick", "min_quantity": 1, "max_quantity": 1, "chance": 0.4},
        {"coins": 3, "chance": 0.55},
    )

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
        xp_reward=10,
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
            color=(200, 35, 35),
            xp_reward=xp_reward,
            **hitbox_kwargs,
        )
        self.preferred_distance = float(preferred_distance)
        self.min_distance = float(min_distance)
        self.attack_range = float(attack_range)
        self.attack_radius = self.attack_range
        self.projectile_speed = float(projectile_speed)
        self.projectile_radius = int(projectile_radius)
        self.projectiles = []
        self.sprite_asset_dir = ASSETS_DIR / "enemies" / "wasp_archer"
        base_frames = self._load_animation_frames(self.sprite_asset_dir / self.SPRITE_SHEET, frame_count=5)
        self.sprite_animations = {
            "idle": base_frames[:1] if base_frames else [],
            "move": base_frames,
            "attack": list(base_frames),
        }
        self.current_animation = "idle"
        self.current_frame_index = 0
        self.animation_frame_timer = 0.0
        self.current_sprite = self.sprite_animations["idle"][0] if self.sprite_animations["idle"] else None
        self.projectile_sprite = load_image(
            self.sprite_asset_dir / self.PROJECTILE_SPRITE,
            size=(self.projectile_radius * 2, self.projectile_radius * 2),
        )
        self.attack_animation_timer = 0.0

    def update(self, dt, game_scene):
        previous_position = Vector2(self.position.x, self.position.y)
        super().update(dt, game_scene)
        if self.is_dead:
            return
        if self.behavior_state != CHASE:
            self._update_projectiles(dt, game_scene)
            moved = (self.position.x != previous_position.x) or (self.position.y != previous_position.y)
            self.attack_animation_timer = max(0.0, self.attack_animation_timer - dt)
            self._update_animation(dt, moved)
            return
        player = game_scene.player
        player_center = player.get_center()
        distance = entity_distance(self, player)
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
        moved = (self.position.x != previous_position.x) or (self.position.y != previous_position.y)
        self.attack_animation_timer = max(0.0, self.attack_animation_timer - dt)
        self._update_animation(dt, moved)

    def _shoot(self, target_x, target_y):
        origin = self.get_center()
        self.attack_animation_timer = 0.16
        self.projectiles.append(
            WaspProjectile(
                origin.x,
                origin.y,
                target_x,
                target_y,
                self.projectile_speed,
                self.damage,
                self.projectile_radius,
                sprite=self.projectile_sprite,
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

    def _load_animation_frames(self, path, frame_count):
        sheet = load_image(path)
        if sheet is None:
            return []
        target_size = self._get_sprite_target_size()
        frame_width, frame_height = self.SPRITE_FRAME_SIZE
        frames = []
        for index in range(frame_count):
            source_rect = pygame.Rect(index * frame_width, 0, frame_width, frame_height)
            if source_rect.right > sheet.get_width():
                break
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), source_rect)
            if target_size != (frame_width, frame_height):
                frame = pygame.transform.scale(frame, target_size)
            frames.append(frame)
        return frames

    def _update_animation(self, dt, moved):
        animation_name = "attack" if self.attack_animation_timer > 0.0 else "move" if moved else "idle"
        frames = self.sprite_animations.get(animation_name, [])
        if not frames:
            self.current_sprite = None
            return
        if self.current_animation != animation_name:
            self.current_animation = animation_name
            self.current_frame_index = 0
            self.animation_frame_timer = 0.0
        frame_duration = self.SPRITE_FRAME_DURATIONS.get(animation_name, 0.12)
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
        sprite = self.current_sprite
        if sprite is None:
            super()._draw_body(screen, camera)
            return
        if self.facing_left != self.SPRITE_NATIVE_FACING_LEFT:
            sprite = pygame.transform.flip(sprite, True, False)
        if self.hurt_flash_timer > 0:
            sprite = sprite.copy()
            sprite.fill((100, 100, 100, 0), special_flags=pygame.BLEND_RGB_ADD)
        self._blit_body_sprite(screen, camera, sprite)

    def draw(self, screen, camera):
        if self.is_dead:
            return
        self._draw_projectiles(screen, camera)
        super().draw(screen, camera)


class WaspProjectile(RangedProjectile):
    POISON_DAMAGE_PER_SECOND = 2.0
    POISON_DURATION = 4.0

    def __init__(self, x, y, target_x, target_y, speed, damage, radius=5, sprite=None):
        super().__init__(x, y, target_x, target_y, speed, damage, radius)
        self.sprite = sprite

    def on_hit_player(self, player):
        player.add_active_effect(
            EffectType.POISON,
            self.POISON_DAMAGE_PER_SECOND,
            self.POISON_DURATION,
        )

    def draw(self, screen, camera):
        if self.is_dead:
            return
        if self.sprite is None:
            super().draw(screen, camera)
            return
        sprite = self.sprite
        angle = -math.degrees(math.atan2(self.direction.y, self.direction.x)) if self.direction.length() > 0 else 0.0
        if abs(angle) > 0.01:
            sprite = pygame.transform.rotate(sprite, angle)
        rect = sprite.get_rect(
            center=(int(self.position.x - camera.position.x), int(self.position.y - camera.position.y))
        )
        screen.blit(sprite, rect.topleft)
