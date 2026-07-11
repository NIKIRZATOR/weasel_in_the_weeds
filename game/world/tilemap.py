from __future__ import annotations

from pathlib import Path

import pygame

from game.core.assets import load_image
from game.world.level import TilesetRenderData
from settings import COLORS, TILE_SIZE


class TileMap:
    """Tile map that supports both legacy color tiles and TMX tilesets."""

    _tileset_cache: dict[Path, pygame.Surface | None] = {}

    TILE_TYPES = {
        0: "grass",
        1: "wall",
        2: "water",
        3: "path",
    }

    def __init__(
        self,
        ground_layer,
        obstacle_layer,
        tile_size=TILE_SIZE,
        tileset: TilesetRenderData | None = None,
    ):
        self.ground_layer = ground_layer
        self.obstacle_layer = obstacle_layer
        self.width = len(ground_layer[0])
        self.height = len(ground_layer)
        self.tile_size = tile_size
        self.tileset = tileset
        self.tileset_surface = self._load_tileset_surface(tileset.image_path) if tileset is not None else None
        self._minimap_surface_cache: dict[int, pygame.Surface] = {}

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

        obstacle = self.obstacle_layer[y][x]
        if obstacle == 1:
            return False
        if obstacle == 2 and not ignore_obstacles:
            return False

        if self.tileset is None and self.ground_layer[y][x] == 1:
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
                if self.tileset is not None and self.tileset_surface is not None:
                    self._draw_tileset_tile(screen, screen_x, screen_y, self.ground_layer[y][x])
                    continue
                self._draw_legacy_tile(screen, screen_x, screen_y, self.ground_layer[y][x], self.obstacle_layer[y][x])

    def build_minimap_surface(self, tile_pixel_size: int = 2) -> pygame.Surface:
        tile_pixel_size = max(1, int(tile_pixel_size))
        cached = self._minimap_surface_cache.get(tile_pixel_size)
        if cached is not None:
            return cached

        surface = pygame.Surface(
            (self.width * tile_pixel_size, self.height * tile_pixel_size),
            pygame.SRCALPHA,
        )
        for y in range(self.height):
            for x in range(self.width):
                preview = self._get_minimap_tile_preview(
                    self.ground_layer[y][x],
                    self.obstacle_layer[y][x],
                    tile_pixel_size,
                )
                if preview is None:
                    continue
                surface.blit(preview, (x * tile_pixel_size, y * tile_pixel_size))
        self._minimap_surface_cache[tile_pixel_size] = surface
        return surface

    def _draw_legacy_tile(self, screen, screen_x, screen_y, tile_type, obstacle):
        color = self.get_tile_color(tile_type)
        pygame.draw.rect(screen, color, (screen_x, screen_y, self.tile_size, self.tile_size))
        pygame.draw.rect(screen, COLORS["BLACK"], (screen_x, screen_y, self.tile_size, self.tile_size), 1)
        if obstacle == 1:
            pygame.draw.ellipse(
                screen,
                COLORS["STONE"],
                (screen_x + 10, screen_y + 20, self.tile_size - 20, self.tile_size - 30),
            )

    def _draw_tileset_tile(self, screen, screen_x, screen_y, gid):
        if gid <= 0 or self.tileset_surface is None or self.tileset is None:
            return

        local_tile_id = gid - self.tileset.firstgid
        if local_tile_id < 0:
            return
        source_x = (local_tile_id % self.tileset.columns) * self.tileset.tile_width
        source_y = (local_tile_id // self.tileset.columns) * self.tileset.tile_height
        source_rect = pygame.Rect(source_x, source_y, self.tileset.tile_width, self.tileset.tile_height)
        if source_rect.right > self.tileset_surface.get_width() or source_rect.bottom > self.tileset_surface.get_height():
            return

        destination_rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
        screen.blit(self.tileset_surface, destination_rect, source_rect)

    def _get_minimap_tile_preview(self, ground_tile, obstacle_tile, tile_pixel_size):
        if self.tileset is not None and self.tileset_surface is not None:
            return self._get_tileset_minimap_tile_preview(ground_tile, tile_pixel_size)
        return self._get_legacy_minimap_tile_preview(ground_tile, obstacle_tile, tile_pixel_size)

    def _get_tileset_minimap_tile_preview(self, gid, tile_pixel_size):
        if gid <= 0 or self.tileset_surface is None or self.tileset is None:
            return None
        local_tile_id = gid - self.tileset.firstgid
        if local_tile_id < 0:
            return None

        source_x = (local_tile_id % self.tileset.columns) * self.tileset.tile_width
        source_y = (local_tile_id // self.tileset.columns) * self.tileset.tile_height
        source_rect = pygame.Rect(source_x, source_y, self.tileset.tile_width, self.tileset.tile_height)
        if source_rect.right > self.tileset_surface.get_width() or source_rect.bottom > self.tileset_surface.get_height():
            return None

        tile_surface = pygame.Surface((self.tileset.tile_width, self.tileset.tile_height), pygame.SRCALPHA)
        tile_surface.blit(self.tileset_surface, (0, 0), source_rect)
        return pygame.transform.smoothscale(tile_surface, (tile_pixel_size, tile_pixel_size))

    def _get_legacy_minimap_tile_preview(self, tile_type, obstacle, tile_pixel_size):
        source_size = 32
        tile_surface = pygame.Surface((source_size, source_size), pygame.SRCALPHA)
        self._draw_legacy_tile(tile_surface, 0, 0, tile_type, obstacle)
        return pygame.transform.smoothscale(tile_surface, (tile_pixel_size, tile_pixel_size))

    @classmethod
    def _load_tileset_surface(cls, image_path: Path):
        if image_path not in cls._tileset_cache:
            cls._tileset_cache[image_path] = load_image(image_path)
        return cls._tileset_cache[image_path]
