from game.objects.world_object import WorldObject
from settings import COLORS


class PickableObject(WorldObject):
    """Объект мира, который можно поднять."""

    def __init__(self, x, y, width, height, name="pickable_object", properties=None):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=COLORS["PICKABLE_OBJECT"],
            is_solid=False,
            is_interactable=True,
            properties=properties,
        )
        self.is_picked = False

    def interact(self, player, game_scene):
        if self.is_picked:
            return False

        self.is_picked = True
        self.is_active = True
        self.color = COLORS["PICKABLE_PICKED"]
        game_scene.last_interaction_message = f"Подобрано: {self.name}"
        game_scene.last_interaction_timer = 1.5
        return True
