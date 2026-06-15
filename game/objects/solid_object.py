from game.objects.world_object import WorldObject
from settings import COLORS


class SolidObject(WorldObject):
    """Объект мира, который блокирует движение."""

    def __init__(self, x, y, width, height, name="solid_object", properties=None):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=COLORS["SOLID_OBJECT"],
            is_solid=True,
            properties=properties,
        )
