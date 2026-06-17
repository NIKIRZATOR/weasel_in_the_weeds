from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


def load_tmx_preview(tmx_path: str | Path) -> dict:
    path = Path(tmx_path)
    root = ET.fromstring(path.read_text(encoding="utf-8"))

    tile_width = int(root.attrib["tilewidth"])
    tile_height = int(root.attrib["tileheight"])
    width = int(root.attrib["width"])
    height = int(root.attrib["height"])

    tilesets = []
    for tileset in root.findall("tileset"):
        tilesets.append(
            {
                "firstgid": int(tileset.attrib.get("firstgid", 1)),
                "source": tileset.attrib.get("source"),
            }
        )

    layers = []
    for layer in root.findall("layer"):
        data_node = layer.find("data")
        if data_node is None or data_node.attrib.get("encoding") != "csv":
            continue

        values = [int(value.strip()) for value in data_node.text.split(",") if value.strip()]
        layer_width = int(layer.attrib["width"])
        grid = [values[index:index + layer_width] for index in range(0, len(values), layer_width)]

        layers.append(
            {
                "name": layer.attrib.get("name", ""),
                "class": layer.attrib.get("class", ""),
                "width": layer_width,
                "height": int(layer.attrib["height"]),
                "sample_row": grid[0][: min(12, len(grid[0]))] if grid else [],
                "grid": grid,
            }
        )

    object_groups = []
    for object_group in root.findall("objectgroup"):
        objects = []
        for obj in object_group.findall("object"):
            properties = _parse_properties(obj.find("properties"))
            pixel_x = float(obj.attrib.get("x", 0))
            pixel_y = float(obj.attrib.get("y", 0))
            object_width = _resolve_object_size(obj.attrib.get("width"), properties.get("width"), tile_width)
            object_height = _resolve_object_size(obj.attrib.get("height"), properties.get("height"), tile_height)

            objects.append(
                {
                    "id": int(obj.attrib.get("id", 0)),
                    "name": obj.attrib.get("name", ""),
                    "type": obj.attrib.get("type", ""),
                    "class": obj.attrib.get("class", ""),
                    "x_px": pixel_x,
                    "y_px": pixel_y,
                    "x_tile": int(pixel_x // tile_width),
                    "y_tile": int(pixel_y // tile_height),
                    "width_tiles": object_width,
                    "height_tiles": object_height,
                    "properties": properties,
                }
            )

        object_groups.append(
            {
                "name": object_group.attrib.get("name", ""),
                "class": object_group.attrib.get("class", ""),
                "objects": objects,
            }
        )

    return {
        "path": str(path),
        "map": {
            "width": width,
            "height": height,
            "tilewidth": tile_width,
            "tileheight": tile_height,
        },
        "tilesets": tilesets,
        "layers": layers,
        "object_groups": object_groups,
        "suggested_level_data": _build_level_data_preview(path, tile_width, layers, object_groups),
    }


def load_tmx_level_data(tmx_path: str | Path) -> dict:
    preview = load_tmx_preview(tmx_path)
    level_data = preview["suggested_level_data"]
    level_data["tileset_image_path"] = _resolve_tileset_image_path(Path(tmx_path), preview["tilesets"])
    return level_data


def preview_to_json(preview: dict) -> str:
    return json.dumps(preview, ensure_ascii=False, indent=2)


def _parse_properties(properties_node: ET.Element | None) -> dict:
    if properties_node is None:
        return {}

    parsed = {}
    for prop in properties_node.findall("property"):
        name = prop.attrib["name"]
        value = prop.attrib.get("value", prop.text or "")
        prop_type = prop.attrib.get("type", "string")

        if prop_type == "int":
            parsed[name] = int(value)
        elif prop_type == "float":
            parsed[name] = float(value)
        elif prop_type == "bool":
            parsed[name] = value.lower() == "true"
        else:
            parsed[name] = value
    return parsed


def _resolve_object_size(raw_size: str | None, property_size, tile_size: int) -> int:
    if property_size not in (None, ""):
        return max(1, int(property_size))
    if raw_size not in (None, ""):
        return max(1, int(round(float(raw_size) / tile_size)))
    return 1


def _build_level_data_preview(path: Path, tile_width: int, layers: list[dict], object_groups: list[dict]) -> dict:
    ground_layer = []
    for layer in layers:
        if layer["class"] == "ground" or not ground_layer:
            ground_layer = layer["grid"]
            if layer["class"] == "ground":
                break

    objects = []
    player_spawn = {"x": 0, "y": 0}
    for object_group in object_groups:
        for obj in object_group["objects"]:
            object_type = obj["type"] or obj["class"]
            if object_type == "player_spawn":
                player_spawn = {"x": obj["x_tile"], "y": obj["y_tile"]}
                continue

            objects.append(
                {
                    "type": object_type,
                    "name": obj["name"],
                    "x": obj["x_tile"],
                    "y": obj["y_tile"],
                    "width": obj["width_tiles"],
                    "height": obj["height_tiles"],
                    "properties": obj["properties"],
                }
            )

    obstacle_layer = [[0 for _ in row] for row in ground_layer]
    return {
        "name": path.stem,
        "tile_size": tile_width,
        "player_spawn": player_spawn,
        "layers": {
            "ground": ground_layer,
            "obstacles": obstacle_layer,
        },
        "objects": objects,
    }


def _resolve_tileset_image_path(tmx_path: Path, tilesets: list[dict]) -> str | None:
    for tileset in tilesets:
        source = tileset.get("source")
        if not source:
            continue

        tsx_path = (tmx_path.parent / source).resolve()
        if tsx_path.exists():
            try:
                tsx_root = ET.fromstring(tsx_path.read_text(encoding="utf-8"))
                image_node = tsx_root.find("image")
                if image_node is not None and image_node.attrib.get("source"):
                    image_path = (tsx_path.parent / image_node.attrib["source"]).resolve()
                    if image_path.exists():
                        return str(image_path)
            except ET.ParseError:
                pass

        fallback_png = (tmx_path.parent / (Path(source).stem + ".png")).resolve()
        if fallback_png.exists():
            return str(fallback_png)

    return None
