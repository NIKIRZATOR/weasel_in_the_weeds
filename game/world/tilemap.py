from pathlib import Path

import pygame

from settings import COLORS, TILE_SIZE


class TileMap:
    """Tilemap rendering and walkability checks."""

    TILE_TYPES = {
        0: "grass",
        1: "wall",
        2: "water",
        3: "path",
    }

    def __init__(self, ground_layer, obstacle_layer, tile_size=TILE_SIZE, tileset_image_path=None):
        self.ground_layer = ground_layer
        self.obstacle_layer = obstacle_layer
        self.width = len(ground_layer[0])
        self.height = len(ground_layer)
        self.tile_size = tile_size
        self.tileset_image_path = tileset_image_path
        self.tile_surfaces = {}
        self._load_tileset()

    def get_tile_type(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.ground_layer[y][x]
        return 1

    def get_obstacle(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.obstacle_layer[y][x]
        return 0

    def get_tile_color(self, tile_type):
        color_map = {
            0: COLORS["GRASS"],
            1: COLORS["WALL"],
            2: COLORS["WATER"],
            3: COLORS["PATH"],
        }
        return color_map.get(tile_type, (255, 0, 255))

    def is_walkable(self, x, y, ignore_obstacles=False):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False

        if self.ground_layer[y][x] == 1:
            return False

        if not ignore_obstacles:
            obstacle = self.obstacle_layer[y][x]
            if obstacle == 1 or obstacle == 2:
                return False

        return True

    def draw(self, screen, camera):
        start_x = max(0, int(camera.position.x // self.tile_size))
        end_x = min(self.width, int((camera.position.x + screen.get_width()) // self.tile_size + 1))
        start_y = max(0, int(camera.position.y // self.tile_size))
        end_y = min(self.height, int((camera.position.y + screen.get_height()) // self.tile_size + 1))

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = x * self.tile_size - camera.position.x
                screen_y = y * self.tile_size - camera.position.y

                tile_gid = self.ground_layer[y][x]
                tile_surface = self.tile_surfaces.get(tile_gid)
                if tile_surface is not None:
                    screen.blit(tile_surface, (screen_x, screen_y))
                else:
                    color = self.get_tile_color(tile_gid)
                    pygame.draw.rect(
                        screen,
                        color,
                        (screen_x, screen_y, self.tile_size, self.tile_size),
                    )
                    pygame.draw.rect(
                        screen,
                        COLORS["BLACK"],
                        (screen_x, screen_y, self.tile_size, self.tile_size),
                        1,
                    )

                obstacle = self.obstacle_layer[y][x]
                if obstacle == 1:
                    pygame.draw.ellipse(
                        screen,
                        COLORS["STONE"],
                        (
                            screen_x + 10,
                            screen_y + 20,
                            self.tile_size - 20,
                            self.tile_size - 30,
                        ),
                    )

    def _load_tileset(self):
        if self.tileset_image_path is None:
            return

        image_path = Path(self.tileset_image_path)
        if not image_path.exists():
            return

        surface = pygame.image.load(str(image_path)).convert_alpha()
        source_tile_size = self.tile_size
        columns = max(1, surface.get_width() // source_tile_size)
        rows = max(1, surface.get_height() // source_tile_size)

        gid = 1
        for row in range(rows):
            for col in range(columns):
                rect = pygame.Rect(
                    col * source_tile_size,
                    row * source_tile_size,
                    source_tile_size,
                    source_tile_size,
                )
                tile = surface.subsurface(rect).copy()
                self.tile_surfaces[gid] = tile
                gid += 1
