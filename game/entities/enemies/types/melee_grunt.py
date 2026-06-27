from __future__ import annotations

import pygame

from game.core.assets import load_image
from game.core.vector import Vector2
from game.entities.enemies.ai.states import CHASE
from game.entities.enemies.ai.steering import entity_distance
from game.entities.enemies.base import Enemy
from settings import ASSETS_DIR


class MeleeGruntEnemy(Enemy):
    SPRITE_FRAME_SIZE = (64, 64)
    SPRITE_FRAME_DURATIONS = {
        "idle": 0.4,
        "move": 0.11,
        "attack": 0.08,
    }
    SPRITE_NATIVE_FACING_LEFT = {
        "idle": False,
        "move": False,
        "attack": False,
    }
    BODY_HITBOX = {
        "width": 48,
        "height": 64, 
        "offset_x": 8,
        "offset_y": 8,
    }
    HURTBOX = {
        "width": 48,
        "height": 64, 
        "offset_x": 8,
        "offset_y": 8,
    }
    ATTACK_HITBOX = None
    COLLISION_CIRCLE = {
        "radius": 10.5,
    }
    LOOT_TABLE = (
        {"item_id": "bone", "min_quantity": 1, "max_quantity": 1, "chance": 0.45},
        {"item_id": "stick", "min_quantity": 1, "max_quantity": 2, "chance": 0.35},
        {"coins": 2, "chance": 0.5},
    )

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
        melee_range=60,
        detection_radius=150,
        attack_cooldown=1.0,
        patrol_radius=140,
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
            color=(220, 55, 55),
            xp_reward=xp_reward,
            **hitbox_kwargs,
        )
        self.attack_reach = float(melee_range)
        self.melee_range = self.attack_reach
        self.attack_radius = self.attack_reach
        self.sprite_asset_dir = ASSETS_DIR / "enemies" / "goat_warrior"
        self.sprite_animations = {
            "idle": self._load_animation_frames(self.sprite_asset_dir / "goat_idle.png", frame_count=1),
            "move": self._load_animation_frames(self.sprite_asset_dir / "goad_steps.png", frame_count=10),
            "attack": self._load_animation_frames(self.sprite_asset_dir / "goat_attack.png", frame_count=4),
        }
        self.current_animation = "idle"
        self.current_frame_index = 0
        self.animation_frame_timer = 0.0
        self.current_sprite = self.sprite_animations["idle"][0] if self.sprite_animations["idle"] else None
        self.attack_animation_timer = 0.0

    def update(self, dt, game_scene):
        previous_position = Vector2(self.position.x, self.position.y)
        super().update(dt, game_scene)
        moved = (self.position.x != previous_position.x) or (self.position.y != previous_position.y)
        self.attack_animation_timer = max(0.0, self.attack_animation_timer - dt)
        self._update_animation(dt, moved)
        if self.is_dead or self.behavior_state != CHASE:
            return
        player = game_scene.player
        player_center = player.get_center()
        distance = entity_distance(self, player)
        if distance <= self.attack_reach:
            if not self.attack_cooldown.is_active():
                attack_direction = Vector2(
                    player_center.x - self.get_center().x,
                    player_center.y - self.get_center().y,
                )
                self._update_facing_from_direction(attack_direction)
                self.attack_animation_timer = 0.22
                player.take_damage(self.damage)
                self.attack_cooldown.start()
            return
        previous_position = Vector2(self.position.x, self.position.y)
        self._move_towards(player_center.x, player_center.y, dt, game_scene, use_pathfinding=True)
        self._update_stuck_state(dt, previous_position, game_scene)

    def _load_animation_frames(self, path, frame_count):
        sheet = load_image(path)
        if sheet is None:
            return []
        target_size = (int(self.width), int(self.height))
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

    def _resolve_animation_name(self, moved):
        if self.attack_animation_timer > 0.0:
            return "attack"
        if moved:
            return "move"
        return "idle"

    def _update_animation(self, dt, moved):
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
        native_facing_left = self.SPRITE_NATIVE_FACING_LEFT.get(self.current_animation, False)
        if self.facing_left != native_facing_left:
            sprite = pygame.transform.flip(sprite, True, False)
        if self.hurt_flash_timer > 0:
            sprite = sprite.copy()
            sprite.fill((100, 100, 100, 0), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(sprite, (self.position.x - camera.position.x, self.position.y - camera.position.y))
