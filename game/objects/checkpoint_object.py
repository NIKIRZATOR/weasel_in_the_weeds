import math

import pygame

from game.core.assets import load_image
from game.objects.world_object import WorldObject
from settings import ASSETS_DIR, COLORS


class CheckpointObject(WorldObject):
    SPRITE_SHEETS = {
        "inactive": ("world_objects/checkpoint_object/checkpoint_stone_no_active.png", 1),
        "activating": ("world_objects/checkpoint_object/checkpoint_stone_activation.png", 6),
        "active": ("world_objects/checkpoint_object/checkpoint_stone_active.png", 8),
    }
    SPRITE_FRAME_DURATIONS_MS = {
        "inactive": 1000,
        "activating": 90,
        "active": 120,
    }
    _ANIMATION_CACHE: dict[tuple[str, int, int], list[pygame.Surface]] = {}

    def __init__(self, x, y, width, height, name="checkpoint_object", properties=None):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=COLORS["STONE"],
            is_solid=False,
            is_interactable=False,
            properties=properties,
        )
        self.is_checkpoint = True
        self.is_activated = False
        self.activation_started_at_ms: int | None = None
        radius_tiles = float(self.properties.get("activation_radius_tiles", 1))
        self.activation_radius = max(0.0, radius_tiles * width)

    def can_activate(self, player):
        if self.is_activated:
            return False

        checkpoint_center = self.get_center()
        player_center = player.get_center()
        distance = math.hypot(
            player_center.x - checkpoint_center.x,
            player_center.y - checkpoint_center.y,
        )
        return distance <= self.activation_radius

    def activate(self, player, game_scene):
        if not self.can_activate(player):
            return False

        respawn_x = self.position.x + self.width
        respawn_y = self.position.y
        player.set_respawn_point(respawn_x, respawn_y)
        self.is_activated = True
        self.activation_started_at_ms = pygame.time.get_ticks()
        game_scene.last_interaction_message = f"Checkpoint activated: {self.name}"
        game_scene.last_interaction_timer = 1.5
        return True

    def draw(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        label_rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        sprite = self._get_checkpoint_sprite()
        if sprite is not None:
            screen.blit(sprite, label_rect.topleft)
            self.draw_debug(screen, camera)
            return
        if self._draw_sprite_if_available(screen, label_rect):
            self.draw_debug(screen, camera)
            return

        points = [
            (screen_x + self.width / 2, screen_y),
            (screen_x, screen_y + self.height),
            (screen_x + self.width, screen_y + self.height),
        ]

        pygame.draw.polygon(screen, COLORS["STONE"], points)
        border_color = COLORS["UI_SLOT_SELECTED"] if self.is_activated else COLORS["BLACK"]
        border_width = 4 if self.is_activated else 2
        pygame.draw.polygon(screen, border_color, points, width=border_width)
        self.draw_name_label(screen, label_rect)
        self.draw_debug(screen, camera)

    def _get_checkpoint_sprite(self):
        state = self._get_animation_state()
        frames = self._load_checkpoint_frames(state)
        if not frames:
            return None
        if state == "inactive":
            return frames[0]

        elapsed_ms = self._get_state_elapsed_ms()
        frame_duration_ms = self.SPRITE_FRAME_DURATIONS_MS[state]
        if state == "activating":
            frame_index = min(len(frames) - 1, elapsed_ms // frame_duration_ms)
            return frames[int(frame_index)]

        frame_index = (elapsed_ms // frame_duration_ms) % len(frames)
        return frames[int(frame_index)]

    def _get_animation_state(self):
        if not self.is_activated:
            return "inactive"
        elapsed_ms = self._get_state_elapsed_ms()
        activation_total_ms = len(self._load_checkpoint_frames("activating")) * self.SPRITE_FRAME_DURATIONS_MS["activating"]
        if elapsed_ms < activation_total_ms:
            return "activating"
        return "active"

    def _get_state_elapsed_ms(self):
        if self.activation_started_at_ms is None:
            return 0
        return max(0, pygame.time.get_ticks() - self.activation_started_at_ms)

    def _load_checkpoint_frames(self, state):
        sprite_path, frame_count = self.SPRITE_SHEETS[state]
        cache_key = (state, int(self.width), int(self.height))
        if cache_key in self._ANIMATION_CACHE:
            return self._ANIMATION_CACHE[cache_key]

        sheet = load_image(ASSETS_DIR / sprite_path)
        if sheet is None:
            self._ANIMATION_CACHE[cache_key] = []
            return []

        frame_width = max(1, sheet.get_width() // max(1, frame_count))
        frame_height = max(1, sheet.get_height())
        frames = []
        for index in range(frame_count):
            source_rect = pygame.Rect(index * frame_width, 0, frame_width, frame_height)
            if source_rect.right > sheet.get_width():
                break
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), source_rect)
            if (frame_width, frame_height) != (self.width, self.height):
                frame = pygame.transform.scale(frame, (int(self.width), int(self.height)))
            frames.append(frame)
        self._ANIMATION_CACHE[cache_key] = frames
        return frames
