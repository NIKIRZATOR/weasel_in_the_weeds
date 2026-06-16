from game.items import get_item_definition
from game.objects.world_object import WorldObject
from settings import COLORS


class PickableObject(WorldObject):
    """Объект мира, который можно поднять."""

    def __init__(self, x, y, width, height, name="pickable_object", properties=None):
        properties = {} if properties is None else properties
        item_id = properties.get("item_id") or name
        definition = get_item_definition(item_id)
        color = COLORS["PICKABLE_OBJECT"]
        if definition is not None:
            if definition.kind.value == "currency":
                color = COLORS["GOLD"]
            elif definition.kind.value in ("weapon", "armor", "accessory"):
                color = COLORS["UI_SLOT_SELECTED"]

        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=color,
            is_solid=False,
            is_interactable=True,
            properties=properties,
        )
        self.is_picked = False

    def interact(self, player, game_scene):
        if self.is_picked:
            return False
        return game_scene.try_pickup_object(self)
