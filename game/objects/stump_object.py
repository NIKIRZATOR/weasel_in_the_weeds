from game.objects.world_object import WorldObject
from settings import COLORS


class StumpObject(WorldObject):
    DEFAULT_SPRITE_SCALE_X = 2.0
    DEFAULT_SPRITE_SCALE_Y = 2.0
    DEFAULT_HITBOX_WIDTH_RATIO = 0.7
    DEFAULT_HITBOX_HEIGHT_RATIO = 0.55
    DEFAULT_HITBOX_LIFT = 0

    def __init__(self, x, y, width, height, name="stump_object", properties=None):
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
        self.is_stump_object = True
