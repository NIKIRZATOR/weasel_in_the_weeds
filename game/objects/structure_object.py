import pygame

from game.core.assets import load_image
from game.objects.world_object import WorldObject
from settings import ASSETS_DIR, COLORS


class StructureObject(WorldObject):
    DEFAULT_SPRITE_SCALE_X = 1.0
    DEFAULT_SPRITE_SCALE_Y = 1.0
    DEFAULT_HITBOX_WIDTH_RATIO = 0.7
    DEFAULT_HITBOX_HEIGHT_RATIO = 0.55
    DEFAULT_HITBOX_LIFT = 0

    def __init__(self, x, y, width, height, name="structure_object", properties=None):
        properties = {} if properties is None else dict(properties)
        sprite_scale_x = max(0.1, float(properties.get("sprite_scale_x", self.DEFAULT_SPRITE_SCALE_X)))
        sprite_scale_y = max(0.1, float(properties.get("sprite_scale_y", self.DEFAULT_SPRITE_SCALE_Y)))
        properties.setdefault("sprite_scale_x", sprite_scale_x)
        properties.setdefault("sprite_scale_y", sprite_scale_y)
        properties.setdefault("sprite_anchor", "bottom_center")
        pixel_offset_x = int(properties.get("pixel_offset_x", 0))
        pixel_offset_y = int(properties.get("pixel_offset_y", 0))

        sprite_width = max(1, int(round(width * sprite_scale_x)))
        sprite_height = max(1, int(round(height * sprite_scale_y)))
        sprite_draw_offset_x = int(round((width - sprite_width) / 2))
        sprite_draw_offset_y = int(round(height - sprite_height))

        hitbox_width_ratio = float(properties.get("hitbox_width_ratio", self.DEFAULT_HITBOX_WIDTH_RATIO))
        hitbox_height_ratio = float(properties.get("hitbox_height_ratio", self.DEFAULT_HITBOX_HEIGHT_RATIO))
        hitbox_lift = int(properties.get("hitbox_lift", self.DEFAULT_HITBOX_LIFT))
        auto_hitbox_width = max(8, round(sprite_width * hitbox_width_ratio))
        auto_hitbox_height = max(8, round(sprite_height * hitbox_height_ratio))
        hitbox_width = int(properties.get("hitbox_width", auto_hitbox_width))
        hitbox_height = int(properties.get("hitbox_height", auto_hitbox_height))
        hitbox_offset_x = int(
            properties.get(
                "hitbox_offset_x",
                round(sprite_draw_offset_x + pixel_offset_x + (sprite_width - hitbox_width) / 2),
            )
        )
        hitbox_offset_y = int(
            properties.get(
                "hitbox_offset_y",
                round(sprite_draw_offset_y + pixel_offset_y + sprite_height - hitbox_height - hitbox_lift),
            )
        )

        properties.setdefault("hitbox_width_ratio", hitbox_width_ratio)
        properties.setdefault("hitbox_height_ratio", hitbox_height_ratio)
        properties.setdefault("hitbox_lift", hitbox_lift)

        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=COLORS["SOLID_OBJECT"],
            is_solid=True,
            hitbox_width=hitbox_width,
            hitbox_height=hitbox_height,
            hitbox_offset_x=hitbox_offset_x,
            hitbox_offset_y=hitbox_offset_y,
            properties=properties,
        )
        self.is_structure_object = True
        self.animation_frames = self._load_animation_frames(properties)
        self.animation_frame_duration = max(0.05, float(properties.get("animation_frame_duration", 0.12)))
        self.animation_frame_timer = 0.0
        self.animation_frame_index = 0

    def update(self, dt, game_scene):
        if len(self.animation_frames) <= 1:
            return
        self.animation_frame_timer += dt
        while self.animation_frame_timer >= self.animation_frame_duration:
            self.animation_frame_timer -= self.animation_frame_duration
            self.animation_frame_index = (self.animation_frame_index + 1) % len(self.animation_frames)

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
        super().draw(screen, camera)

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
