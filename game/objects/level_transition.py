import pygame

from game.core.assets import load_image
from game.localization import get_localizer
from game.objects.world_object import WorldObject
from settings import ASSETS_DIR, COLORS


class LevelTransition(WorldObject):
    def __init__(self, x, y, width, height, name="level_transition", properties=None):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=(90, 130, 230),
            is_solid=False,
            is_interactable=False,
            properties=properties,
        )
        self.is_transition = True
        self.animation_frames = self._load_animation_frames(self.properties)
        self.animation_frame_duration = max(0.05, float(self.properties.get("animation_frame_duration", 0.18)))
        self.animation_frame_timer = 0.0
        self.animation_frame_index = 0

    def can_activate(self, player):
        return (
            self._has_required_items(player)
            and self._has_required_coins(player)
            and self._has_required_flags(player)
        )

    def get_block_message(self):
        localizer = get_localizer()
        message_key = self.properties.get("blocked_message_key")
        if message_key:
            return localizer.t(str(message_key))
        return self.properties.get("blocked_message", localizer.t("pickup.path_blocked"))

    def get_target_level(self):
        return self.properties.get("target_level")

    def get_target_spawn(self):
        spawn = self.properties.get("target_spawn")
        if not spawn:
            return None
        return int(spawn.get("x", 0)), int(spawn.get("y", 0))

    def get_flags_to_set(self):
        return [str(flag) for flag in self.properties.get("set_flags", []) if flag]

    def update(self, dt, game_scene):
        if len(self.animation_frames) <= 1:
            return
        self.animation_frame_timer += dt
        while self.animation_frame_timer >= self.animation_frame_duration:
            self.animation_frame_timer -= self.animation_frame_duration
            self.animation_frame_index = (self.animation_frame_index + 1) % len(self.animation_frames)

    def _has_required_items(self, player):
        required_items = self.properties.get("required_items", [])
        for requirement in required_items:
            if isinstance(requirement, str):
                item_id = requirement
                quantity = 1
            else:
                item_id = requirement.get("item_id")
                quantity = int(requirement.get("quantity", 1))

            if not item_id or not player.has_item(item_id, quantity):
                return False
        return True

    def _has_required_coins(self, player):
        required_coins = int(self.properties.get("required_coins", 0))
        return player.coins >= required_coins

    def _has_required_flags(self, player):
        required_flags = self.properties.get("required_flags", [])
        return player.has_flags(required_flags)

    def draw(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        if self.animation_frames:
            sprite = self.animation_frames[self.animation_frame_index % len(self.animation_frames)]
            screen.blit(sprite, self._get_sprite_draw_position(rect, sprite))
            self.draw_name_label(screen, rect)
            self.draw_debug(screen, camera)
            return
        if self._draw_sprite_if_available(screen, rect):
            self.draw_name_label(screen, rect)
            self.draw_debug(screen, camera)
            return

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((90, 130, 230, 70))
        screen.blit(overlay, rect.topleft)
        pygame.draw.rect(screen, COLORS["WHITE"], rect, width=2, border_radius=6)
        self.draw_name_label(screen, rect)
        self.draw_debug(screen, camera)

    def _load_animation_frames(self, properties):
        sprite_sheet_path = properties.get("sprite_sheet_path")
        frame_count = int(properties.get("animation_frame_count", 0))
        frame_width = int(properties.get("animation_frame_width", 64))
        frame_height = int(properties.get("animation_frame_height", 64))
        if not sprite_sheet_path or frame_count <= 0:
            return []
        sheet = load_image(ASSETS_DIR / str(sprite_sheet_path))
        if sheet is None:
            return []
        target_size = self._get_sprite_draw_size()
        frames = []
        for index in range(frame_count):
            source_rect = pygame.Rect(index * frame_width, 0, frame_width, frame_height)
            if source_rect.right > sheet.get_width() or source_rect.bottom > sheet.get_height():
                break
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), source_rect)
            if target_size != (frame_width, frame_height):
                frame = pygame.transform.scale(frame, target_size)
            if self.flip_x:
                frame = pygame.transform.flip(frame, True, False)
            frames.append(frame)
        return frames
