from __future__ import annotations

import pygame

from game.localization import get_localizer
from game.scenes.base import Scene
from settings import COLORS


class MapScene(Scene):
    def __init__(self, app, game_scene):
        self.app = app
        self.game_scene = game_scene
        self.player = game_scene.player
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 44)
        self.text_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_m):
                self.app.set_scene(self.game_scene)

    def update(self, dt):
        return None

    def draw(self):
        self.game_scene.draw()

        screen_width, screen_height = self.app.get_screen_size()
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.app.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(48, 48, screen_width - 96, screen_height - 96)
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], panel_rect, border_radius=16)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], panel_rect, width=2, border_radius=16)

        title = self.title_font.render(self.localizer.t("ui.map.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, (panel_rect.x + 24, panel_rect.y + 18))

        hint = self.text_font.render(self.localizer.t("ui.map.close_hint"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(hint, (panel_rect.right - hint.get_width() - 24, panel_rect.y + 24))

        map_rect = pygame.Rect(panel_rect.x + 24, panel_rect.y + 76, panel_rect.width - 48, panel_rect.height - 120)
        pygame.draw.rect(self.app.screen, (18, 22, 28), map_rect, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], map_rect, width=1, border_radius=12)
        self._draw_level_map(map_rect)

    def on_language_changed(self):
        return None

    def _draw_level_map(self, map_rect):
        level = self.game_scene.level
        visited = self.player.get_map_state(self.game_scene.level_key, level.width, level.height)
        if visited is None:
            return

        tile_size = min(map_rect.width / level.width, map_rect.height / level.height)
        tile_size = max(6, int(tile_size))
        draw_width = tile_size * level.width
        draw_height = tile_size * level.height
        origin_x = map_rect.x + (map_rect.width - draw_width) // 2
        origin_y = map_rect.y + (map_rect.height - draw_height) // 2

        fog_surface = pygame.Surface((draw_width, draw_height), pygame.SRCALPHA)

        for row in range(level.height):
            for col in range(level.width):
                rect = pygame.Rect(
                    origin_x + col * tile_size,
                    origin_y + row * tile_size,
                    tile_size,
                    tile_size,
                )
                color = self._resolve_tile_color(level.ground_layer[row][col], level.obstacle_layer[row][col])
                pygame.draw.rect(self.app.screen, color, rect)

                if tile_size >= 10:
                    pygame.draw.rect(self.app.screen, (10, 10, 10), rect, width=1)

                if not visited[row][col]:
                    fog_rect = pygame.Rect(col * tile_size, row * tile_size, tile_size, tile_size)
                    fog_surface.fill((0, 0, 0, 220), fog_rect)

        self.app.screen.blit(fog_surface, (origin_x, origin_y))
        self._draw_player_marker(origin_x, origin_y, tile_size)

        level_name = self.game_scene._localized_level_name()
        area_name = self.small_font.render(level_name, True, COLORS["WHITE"])
        self.app.screen.blit(area_name, (map_rect.x + 12, map_rect.bottom - area_name.get_height() - 10))

    def _draw_player_marker(self, origin_x, origin_y, tile_size):
        tile_x = int(self.player.get_center().x // self.game_scene.level.tile_size)
        tile_y = int(self.player.get_center().y // self.game_scene.level.tile_size)

        center_x = origin_x + tile_x * tile_size + tile_size / 2
        center_y = origin_y + tile_y * tile_size + tile_size / 2
        radius = max(4, tile_size // 3)

        pygame.draw.circle(self.app.screen, (255, 120, 120), (int(center_x), int(center_y)), radius)
        pygame.draw.circle(self.app.screen, COLORS["WHITE"], (int(center_x), int(center_y)), radius, width=2)

    def _resolve_tile_color(self, ground_tile, obstacle_tile):
        if obstacle_tile == 1:
            return (125, 125, 125)
        if obstacle_tile == 2:
            return (85, 62, 34)

        if ground_tile == 1:
            return (82, 88, 92)
        if ground_tile == 2:
            return (55, 110, 170)
        if ground_tile == 3:
            return (154, 129, 88)
        return (68, 124, 64)
