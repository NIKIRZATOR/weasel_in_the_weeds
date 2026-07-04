import json
from dataclasses import dataclass
from pathlib import Path
import random
import xml.etree.ElementTree as ET

from game.objects.solid_object_catalog import get_solid_object_set, get_solid_object_template


@dataclass
class TilesetRenderData:
    image_path: Path
    firstgid: int
    columns: int
    tile_width: int
    tile_height: int
    collision_by_gid: dict[int, int]
    properties_by_gid: dict[int, dict[str, object]]


@dataclass
class LevelData:
    name: str
    tile_size: int
    player_spawn: tuple[int, int]
    ground_layer: list[list[int]]
    obstacle_layer: list[list[int]]
    objects: list[dict]
    tileset: TilesetRenderData | None = None

    @property
    def width(self) -> int:
        return len(self.ground_layer[0])

    @property
    def height(self) -> int:
        return len(self.ground_layer)


def _validate_layer(name: str, layer: list[list[int]]) -> tuple[int, int]:
    if not layer or not layer[0]:
        raise ValueError(f"Level layer '{name}' must not be empty")

    width = len(layer[0])
    for row_index, row in enumerate(layer):
        if len(row) != width:
            raise ValueError(
                f"Level layer '{name}' has non-rectangular row at index {row_index}"
            )

    return width, len(layer)


def load_level(level_path: str | Path) -> LevelData:
    path = Path(level_path)
    if path.is_dir():
        return _load_tmx_level_dir(path)
    raw_level = json.loads(path.read_text(encoding="utf-8"))

    layers = raw_level["layers"]
    ground_layer = layers["ground"]
    obstacle_layer = layers["obstacles"]

    ground_width, ground_height = _validate_layer("ground", ground_layer)
    obstacle_width, obstacle_height = _validate_layer("obstacles", obstacle_layer)

    if (ground_width, ground_height) != (obstacle_width, obstacle_height):
        raise ValueError("Ground and obstacle layers must have the same size")

    player_spawn = raw_level.get("player_spawn", {"x": 0, "y": 0})

    return LevelData(
        name=raw_level.get("name", path.stem),
        tile_size=raw_level.get("tile_size", 64),
        player_spawn=(player_spawn["x"], player_spawn["y"]),
        ground_layer=ground_layer,
        obstacle_layer=obstacle_layer,
        objects=raw_level.get("objects", []),
    )


def _load_tmx_level_dir(level_dir: Path) -> LevelData:
    tmx_path = level_dir / f"{level_dir.name}.tmx"
    if not tmx_path.exists():
        raise FileNotFoundError(f"TMX level file not found: {tmx_path}")

    root = ET.fromstring(tmx_path.read_text(encoding="utf-8"))
    width = int(root.attrib["width"])
    height = int(root.attrib["height"])
    tile_width = int(root.attrib["tilewidth"])
    tile_height = int(root.attrib["tileheight"])
    if tile_width != tile_height:
        raise ValueError("Only square tiles are supported for TMX levels")

    tileset_element = root.find("tileset")
    if tileset_element is None:
        raise ValueError(f"TMX level '{tmx_path}' does not contain a tileset")

    firstgid = int(tileset_element.attrib.get("firstgid", 1))
    columns = int(tileset_element.attrib["columns"])
    tileset_name = tileset_element.attrib.get("name", level_dir.name)
    tileset_image_path = level_dir / f"{tileset_name}.png"
    if not tileset_image_path.exists():
        candidate = level_dir / "world_tile_set.png"
        tileset_image_path = candidate if candidate.exists() else tileset_image_path
    if not tileset_image_path.exists():
        raise FileNotFoundError(f"Tileset image not found for TMX level: {tileset_image_path}")

    properties_by_gid = _parse_tileset_tile_properties(tileset_element, firstgid)
    collision_by_gid = _parse_tileset_collision(tileset_element, firstgid, properties_by_gid)
    ground_layer = _parse_tmx_ground_layer(root, width, height)
    obstacle_layer = [
        [collision_by_gid.get(tile_gid, 0) for tile_gid in row]
        for row in ground_layer
    ]
    player_spawn = _parse_tmx_player_spawn(root, tile_width, tile_height)
    objects = _load_level_dir_objects(level_dir)
    generated_objects = _generate_tmx_decor_objects(
        level_name=root.attrib.get("name", level_dir.name),
        ground_layer=ground_layer,
        tile_size=tile_width,
        tile_properties_by_gid=properties_by_gid,
        collision_by_gid=collision_by_gid,
        existing_objects=objects,
    )
    objects = generated_objects + objects

    return LevelData(
        name=root.attrib.get("name", level_dir.name),
        tile_size=tile_width,
        player_spawn=player_spawn,
        ground_layer=ground_layer,
        obstacle_layer=obstacle_layer,
        objects=objects,
        tileset=TilesetRenderData(
            image_path=tileset_image_path,
            firstgid=firstgid,
            columns=columns,
            tile_width=tile_width,
            tile_height=tile_height,
            collision_by_gid=collision_by_gid,
            properties_by_gid=properties_by_gid,
        ),
    )


def _parse_tmx_ground_layer(root: ET.Element, width: int, height: int) -> list[list[int]]:
    layer_element = root.find("layer")
    if layer_element is None:
        raise ValueError("TMX level must contain at least one tile layer")
    data_element = layer_element.find("data")
    if data_element is None or data_element.attrib.get("encoding") != "csv":
        raise ValueError("TMX layer data must use CSV encoding")
    raw_values = [value.strip() for value in (data_element.text or "").replace("\n", "").split(",")]
    values = [int(value) for value in raw_values if value]
    expected_count = width * height
    if len(values) != expected_count:
        raise ValueError(f"TMX layer has {len(values)} gids, expected {expected_count}")
    return [values[row_start:row_start + width] for row_start in range(0, expected_count, width)]


def _parse_tileset_tile_properties(tileset_element: ET.Element, firstgid: int) -> dict[int, dict[str, object]]:
    properties_by_gid: dict[int, dict[str, object]] = {}
    for tile_element in tileset_element.findall("tile"):
        local_tile_id = int(tile_element.attrib["id"])
        gid = firstgid + local_tile_id
        properties = _parse_tmx_properties(tile_element.find("properties"))
        if properties:
            properties_by_gid[gid] = properties
    return properties_by_gid


def _parse_tileset_collision(
    tileset_element: ET.Element,
    firstgid: int,
    properties_by_gid: dict[int, dict[str, object]] | None = None,
) -> dict[int, int]:
    collision_by_gid: dict[int, int] = {}
    for tile_element in tileset_element.findall("tile"):
        local_tile_id = int(tile_element.attrib["id"])
        gid = firstgid + local_tile_id
        properties = properties_by_gid.get(gid, {}) if properties_by_gid is not None else _parse_tmx_properties(tile_element.find("properties"))
        collision_kind = str(properties.get("collision", "")).strip().lower()
        if collision_kind == "hard":
            collision_by_gid[gid] = 1
            continue
        if collision_kind == "jumpable":
            collision_by_gid[gid] = 2
            continue

        # Legacy fallback: tiles with collision geometry are treated as hard blockers.
        if tile_element.find("objectgroup") is not None:
            collision_by_gid[gid] = 1
    return collision_by_gid


def _parse_tmx_player_spawn(root: ET.Element, tile_width: int, tile_height: int) -> tuple[int, int]:
    object_groups = root.findall("objectgroup")
    for object_group in object_groups:
        for object_element in object_group.findall("object"):
            properties = _parse_tmx_properties(object_element.find("properties"))
            object_type = properties.get("type") or object_element.attrib.get("type") or object_element.attrib.get("name")
            if object_type != "player_spawn":
                continue
            x = int(float(object_element.attrib.get("x", 0)) // tile_width)
            y = int(float(object_element.attrib.get("y", 0)) // tile_height)
            return x, y
    return 0, 0


def _load_level_dir_objects(level_dir: Path) -> list[dict]:
    objects_path = level_dir / "objects.json"
    if not objects_path.exists():
        return []
    raw_objects = json.loads(objects_path.read_text(encoding="utf-8"))
    return raw_objects.get("objects", [])


def _generate_tmx_decor_objects(
    level_name: str,
    ground_layer: list[list[int]],
    tile_size: int,
    tile_properties_by_gid: dict[int, dict[str, object]],
    collision_by_gid: dict[int, int],
    existing_objects: list[dict],
) -> list[dict]:
    occupied_tiles = _collect_occupied_tiles(existing_objects)
    generated_objects: list[dict] = []
    for tile_y, row in enumerate(ground_layer):
        for tile_x, tile_gid in enumerate(row):
            if tile_gid <= 0 or (tile_x, tile_y) in occupied_tiles:
                continue
            if collision_by_gid.get(tile_gid, 0) != 0:
                continue

            tile_properties = tile_properties_by_gid.get(tile_gid, {})
            generated_object = _build_generated_decor_object(
                level_name=level_name,
                tile_gid=tile_gid,
                tile_x=tile_x,
                tile_y=tile_y,
                tile_size=tile_size,
                tile_properties=tile_properties,
            )
            if generated_object is None:
                continue

            generated_objects.append(generated_object)
            occupied_tiles.add((tile_x, tile_y))
    return generated_objects


def _collect_occupied_tiles(objects: list[dict]) -> set[tuple[int, int]]:
    occupied_tiles: set[tuple[int, int]] = set()
    for raw_object in objects:
        start_x = int(raw_object.get("x", 0))
        start_y = int(raw_object.get("y", 0))
        width = max(1, int(raw_object.get("width", 1)))
        height = max(1, int(raw_object.get("height", 1)))
        for tile_y in range(start_y, start_y + height):
            for tile_x in range(start_x, start_x + width):
                occupied_tiles.add((tile_x, tile_y))
    return occupied_tiles


def _build_generated_decor_object(level_name, tile_gid, tile_x, tile_y, tile_size, tile_properties):
    object_id = str(tile_properties.get("decor_object", "")).strip()
    decor_set = str(tile_properties.get("decor_set", "")).strip()
    if not object_id and not decor_set:
        return None

    chance = float(tile_properties.get("decor_chance", tile_properties.get("decor_density", 1.0)))
    if chance <= 0:
        return None

    rng = random.Random(f"{level_name}:{tile_gid}:{tile_x}:{tile_y}")
    if rng.random() > chance:
        return None

    template_id = object_id or _choose_weighted_template_id(decor_set, rng)
    if not template_id:
        return None

    template = get_solid_object_template(template_id)
    if template is None:
        return None

    width = max(1, int(template.get("width", 1)))
    height = max(1, int(template.get("height", 1)))
    pixel_offset_x = int(tile_properties.get("decor_offset_x", 0))
    pixel_offset_y = int(tile_properties.get("decor_offset_y", 0))
    jitter = int(tile_properties.get("decor_jitter", 0))
    if jitter > 0:
        pixel_offset_x += rng.randint(-jitter, jitter)
        pixel_offset_y += rng.randint(-jitter, jitter)

    return {
        "id": f"generated:{template_id}:{tile_x}:{tile_y}",
        "type": "solid_object",
        "name": template.get("name", template_id),
        "x": tile_x,
        "y": tile_y,
        "width": width,
        "height": height,
        "solid": bool(template.get("solid", False)),
        "properties": {
            "sprite_path": template.get("sprite_path"),
            "display_name": "",
            "show_name_with_sprite": False,
            "generated_from_tile_gid": tile_gid,
            "pixel_offset_x": pixel_offset_x,
            "pixel_offset_y": pixel_offset_y,
        },
    }


def _choose_weighted_template_id(set_id: str, rng: random.Random) -> str | None:
    entries = get_solid_object_set(set_id)
    if not entries:
        return None
    total_weight = sum(max(0, int(entry.get("weight", 1))) for entry in entries)
    if total_weight <= 0:
        return None
    pick = rng.uniform(0, total_weight)
    current = 0.0
    for entry in entries:
        current += max(0, int(entry.get("weight", 1)))
        if pick <= current:
            return str(entry.get("object_id", "")).strip() or None
    return str(entries[-1].get("object_id", "")).strip() or None


def _parse_tmx_properties(properties_element: ET.Element | None) -> dict[str, object]:
    if properties_element is None:
        return {}
    result: dict[str, object] = {}
    for property_element in properties_element.findall("property"):
        name = property_element.attrib.get("name")
        if not name:
            continue
        raw_value = property_element.attrib.get("value", property_element.text or "")
        value_type = property_element.attrib.get("type", "string")
        result[name] = _parse_tmx_property_value(raw_value, value_type)
    return result


def _parse_tmx_property_value(raw_value: str, value_type: str) -> object:
    normalized_type = str(value_type or "string").strip().lower()
    if normalized_type == "bool":
        return str(raw_value).strip().lower() in {"1", "true", "yes"}
    if normalized_type in {"int", "integer"}:
        return int(raw_value)
    if normalized_type == "float":
        return float(raw_value)
    return raw_value
