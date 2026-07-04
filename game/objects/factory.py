from game.objects.checkpoint_object import CheckpointObject
from game.objects.container_object import ContainerObject
from game.objects.gatherable_catalog import get_gatherable_template
from game.objects.gatherable_object import GatherableObject
from game.objects.grass_hide_zone import GrassHideZone
from game.objects.interactable_object import InteractableObject
from game.objects.level_transition import LevelTransition
from game.objects.npc_object import NpcObject
from game.objects.pickable_object import PickableObject
from game.objects.solid_object import SolidObject

CONTAINER_SPRITES = {
    "crate": "world_objects/container_object/crate.png",
    "chest": "world_objects/container_object/chest.png",
    "large_chest": "world_objects/container_object/large_chest.png",
}

GATHERABLE_TEMPLATE_SPRITES = {
    "berry_bush_small": "world_objects/gatherable_object/berry_bush.png",
    "fallen_log_small": "world_objects/gatherable_object/fallen_log.png",
    "stone_pile_small": "world_objects/gatherable_object/stone_pile.png",
    "bug_remains_small": "world_objects/gatherable_object/stump.png",
}

PICKABLE_SPRITES = {
    "coin": "world_objects/pickable_object/coin.png",
    "stick": "world_objects/pickable_object/stick.png",
}

SOLID_OBJECT_SPRITES = {
    "stone block": "world_objects/solid_object/stone_block.png",
    "bush": "world_objects/solid_object/bush.png",
    "blue flower": "world_objects/solid_object/flower_blue.png",
    "pink flower": "world_objects/solid_object/flower_pink.png",
    "red white flower": "world_objects/solid_object/flower_red_white.png",
    "white flower": "world_objects/solid_object/flower_white.png",
    "yellow flower": "world_objects/solid_object/flower_yellow.png",
    "stone pile": "world_objects/solid_object/stone_pile.png",
}


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
    properties = dict(properties)
    if raw_object.get("id"):
        properties.setdefault("object_id", str(raw_object["id"]))
    if object_type == "gatherable_object":
        properties = _resolve_gatherable_properties(name, properties)
    _assign_default_sprite_path(object_type, name, properties)

    if object_type == "solid_object":
        world_object = SolidObject(x, y, width, height, name=name, properties=properties)
        raw_solid = raw_object.get("solid")
        if raw_solid is not None:
            world_object.is_solid = bool(raw_solid)
        elif "solid" in properties:
            world_object.is_solid = bool(properties.get("solid"))
        return world_object

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

    if object_type == "container_object":
        return ContainerObject(
            x,
            y,
            width,
            height,
            name=name,
            is_solid=raw_object.get("solid", True),
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

    if object_type == "gatherable_object":
        return GatherableObject(
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


def _resolve_gatherable_properties(name, properties):
    template_id = properties.get("template")
    if not template_id:
        return properties

    template_properties = get_gatherable_template(template_id)
    if template_properties is None:
        return properties

    merged = dict(template_properties)
    merged.update(properties)
    merged["template_id"] = str(template_id)
    merged.pop("template", None)
    return merged


def _assign_default_sprite_path(object_type, name, properties):
    if properties.get("sprite_path"):
        return

    if object_type == "container_object":
        sprite_path = CONTAINER_SPRITES.get(str(properties.get("container_type", "")))
        if sprite_path:
            properties["sprite_path"] = sprite_path
        return

    if object_type == "gatherable_object":
        template_id = str(properties.get("template_id", ""))
        sprite_path = GATHERABLE_TEMPLATE_SPRITES.get(template_id)
        if not sprite_path and template_id == "grass_patch_small":
            sprite_path = "world_objects/solid_object/bush.png"
        if sprite_path:
            properties["sprite_path"] = sprite_path
        return

    if object_type == "solid_object":
        sprite_path = SOLID_OBJECT_SPRITES.get(str(name or "").strip().lower())
        if sprite_path:
            properties["sprite_path"] = sprite_path
        return

    if object_type == "grass_hide_zone":
        properties["sprite_path"] = "world_objects/grass_hide_zone/big_grass.png"
        return

    if object_type == "pickable_object":
        item_id = str(properties.get("item_id") or name or "")
        sprite_path = PICKABLE_SPRITES.get(item_id.lower())
        if sprite_path:
            properties["sprite_path"] = sprite_path
