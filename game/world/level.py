import json
from dataclasses import dataclass
from pathlib import Path

from game.world.tmx_loader import load_tmx_level_data


@dataclass
class LevelData:
    name: str
    tile_size: int
    player_spawn: tuple[int, int]
    ground_layer: list[list[int]]
    obstacle_layer: list[list[int]]
    objects: list[dict]
    tileset_image_path: str | None = None

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
    if path.suffix.lower() == ".tmx":
        raw_level = load_tmx_level_data(path)
    else:
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
        tileset_image_path=raw_level.get("tileset_image_path"),
    )
