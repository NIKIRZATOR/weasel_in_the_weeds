from game.objects.checkpoint_object import CheckpointObject
from game.objects.grass_hide_zone import GrassHideZone
from game.objects.interactable_object import InteractableObject
from game.objects.level_transition import LevelTransition
from game.objects.npc_object import NpcObject
from game.objects.pickable_object import PickableObject
from game.objects.solid_object import SolidObject


def _resolve_dimensions(raw_object, tile_size):
    width = raw_object.get("width", 1) * tile_size
    height = raw_object.get("height", 1) * tile_size
    x = raw_object.get("x", 0) * tile_size
    y = raw_object.get("y", 0) * tile_size
    return x, y, width, height


def create_world_object(raw_object, tile_size):
    object_type = raw_object.get("type")
    if object_type == "player_spawn":
        return None

    x, y, width, height = _resolve_dimensions(raw_object, tile_size)
    name = raw_object.get("name", object_type or "object")
    properties = raw_object.get("properties", {})

    if object_type == "solid_object":
        return SolidObject(x, y, width, height, name=name, properties=properties)

    if object_type == "interactable_object":
        is_solid = raw_object.get("solid", False)
        return InteractableObject(
            x,
            y,
            width,
            height,
            name=name,
            is_solid=is_solid,
            properties=properties,
        )

    if object_type == "pickable_object":
        return PickableObject(
            x,
            y,
            width,
            height,
            name=name,
            properties=properties,
        )

    if object_type == "checkpoint_object":
        return CheckpointObject(
            x,
            y,
            width,
            height,
            name=name,
            properties=properties,
        )
    if object_type == "grass_hide_zone":
        return GrassHideZone(
            x,
            y,
            width,
            height,
            name=name,
            properties=properties,
        )
    if object_type == "level_transition":
        return LevelTransition(
            x,
            y,
            width,
            height,
            name=name,
            properties=properties,
        )

    if object_type == "npc_object":
        return NpcObject(
            x,
            y,
            width,
            height,
            name=name,
            properties=properties,
        )

    return None
