import pygame

from game.objects.world_object import WorldObject
from settings import COLORS


class TreeObject(WorldObject):
    DEFAULT_SPRITE_SCALE_X = 3.0
    DEFAULT_SPRITE_SCALE_Y = 4.0
    DEFAULT_TRUNK_WIDTH_RATIO = 0.24
    DEFAULT_TRUNK_HEIGHT_RATIO = 0.28
    DEFAULT_TRUNK_HITBOX_LIFT = 16
    DEFAULT_CANOPY_OVERLAY_RATIO = 0.68

    def __init__(self, x, y, width, height, name="tree_object", properties=None):
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

        trunk_width = max(8, int(round(sprite_width * float(properties.get("trunk_width_ratio", self.DEFAULT_TRUNK_WIDTH_RATIO)))))
        trunk_height = max(8, int(round(sprite_height * float(properties.get("trunk_height_ratio", self.DEFAULT_TRUNK_HEIGHT_RATIO)))))
        trunk_hitbox_lift = int(properties.get("trunk_hitbox_lift", self.DEFAULT_TRUNK_HITBOX_LIFT))
        hitbox_width = int(properties.get("hitbox_width", trunk_width))
        hitbox_height = int(properties.get("hitbox_height", trunk_height))
        hitbox_offset_x = int(
            properties.get(
                "hitbox_offset_x",
                round(sprite_draw_offset_x + pixel_offset_x + (sprite_width - hitbox_width) / 2),
            )
        )
        hitbox_offset_y = int(
            properties.get(
                "hitbox_offset_y",
                round(sprite_draw_offset_y + pixel_offset_y + sprite_height - hitbox_height - trunk_hitbox_lift),
            )
        )

        properties.setdefault("trunk_width_ratio", float(properties.get("trunk_width_ratio", self.DEFAULT_TRUNK_WIDTH_RATIO)))
        properties.setdefault("trunk_height_ratio", float(properties.get("trunk_height_ratio", self.DEFAULT_TRUNK_HEIGHT_RATIO)))
        properties.setdefault("trunk_hitbox_lift", trunk_hitbox_lift)

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
        self.is_tree_object = True
        self.canopy_overlay_ratio = max(0.1, min(0.95, float(self.properties.get("canopy_overlay_ratio", self.DEFAULT_CANOPY_OVERLAY_RATIO))))

    def has_overlay_pass(self):
        return True

    def draw(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        if self._draw_sprite_base(screen, rect):
            self.draw_name_label(screen, rect)
            return
        pygame.draw.rect(screen, self.color, rect, border_radius=6)
        pygame.draw.rect(screen, COLORS["BLACK"], rect, width=2, border_radius=6)
        self.draw_name_label(screen, rect)

    def draw_overlay(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        self._draw_sprite_overlay(screen, rect)
        self.draw_debug(screen, camera)

    def _draw_sprite_base(self, screen, rect):
        sprite = self._get_sprite_surface()
        if sprite is None:
            return False
        draw_x, draw_y = self._get_sprite_draw_position(rect, sprite)
        split_y = int(round(sprite.get_height() * self.canopy_overlay_ratio))
        split_y = max(0, min(sprite.get_height(), split_y))
        base_height = sprite.get_height() - split_y
        if base_height <= 0:
            return False
        source_rect = pygame.Rect(0, split_y, sprite.get_width(), base_height)
        dest_y = draw_y + split_y
        screen.blit(sprite, (draw_x, dest_y), source_rect)
        return True

    def _draw_sprite_overlay(self, screen, rect):
        sprite = self._get_sprite_surface()
        if sprite is None:
            return False
        draw_x, draw_y = self._get_sprite_draw_position(rect, sprite)
        split_y = int(round(sprite.get_height() * self.canopy_overlay_ratio))
        split_y = max(0, min(sprite.get_height(), split_y))
        if split_y <= 0:
            return False
        source_rect = pygame.Rect(0, 0, sprite.get_width(), split_y)
        screen.blit(sprite, (draw_x, draw_y), source_rect)
        return True
