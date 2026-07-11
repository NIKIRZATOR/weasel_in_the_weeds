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

        level = self.game_scene.level
        raw_map_surface = self.game_scene.tilemap.build_minimap_surface(tile_pixel_size=2)
        raw_width = max(1, raw_map_surface.get_width())
        raw_height = max(1, raw_map_surface.get_height())
        available_width = max(240, screen_width - 96)
        available_height = max(240, screen_height - 96 - 120)
        map_scale = min(available_width / raw_width, available_height / raw_height)
        draw_width = max(1, int(raw_width * map_scale))
        draw_height = max(1, int(raw_height * map_scale))

        panel_padding_x = 28
        panel_padding_top = 76
        panel_padding_bottom = 44
        panel_width = min(screen_width - 48, draw_width + panel_padding_x * 2)
        panel_height = min(screen_height - 48, draw_height + panel_padding_top + panel_padding_bottom)
        panel_rect = pygame.Rect(
            (screen_width - panel_width) // 2,
            (screen_height - panel_height) // 2,
            panel_width,
            panel_height,
        )
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], panel_rect, border_radius=16)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], panel_rect, width=2, border_radius=16)

        title = self.title_font.render(self.localizer.t("ui.map.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, (panel_rect.x + 24, panel_rect.y + 18))

        hint = self.text_font.render(self.localizer.t("ui.map.close_hint"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(hint, (panel_rect.right - hint.get_width() - 24, panel_rect.y + 24))

        map_rect = pygame.Rect(
            panel_rect.x + panel_padding_x,
            panel_rect.y + panel_padding_top,
            draw_width,
            draw_height,
        )
        pygame.draw.rect(self.app.screen, (18, 22, 28), map_rect, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], map_rect, width=1, border_radius=12)
        self._draw_level_map(map_rect, raw_map_surface)

    def on_language_changed(self):
        return None

    def _draw_level_map(self, map_rect, raw_map_surface=None):
        level = self.game_scene.level
        visited = self.player.get_map_state(self.game_scene.level_key, level.width, level.height)
        if visited is None:
            return

        if raw_map_surface is None:
            raw_map_surface = self.game_scene.tilemap.build_minimap_surface(tile_pixel_size=2)
        raw_width = max(1, raw_map_surface.get_width())
        raw_height = max(1, raw_map_surface.get_height())
        scale = min(map_rect.width / raw_width, map_rect.height / raw_height)
        draw_width = max(1, int(raw_width * scale))
        draw_height = max(1, int(raw_height * scale))
        origin_x = map_rect.x + (map_rect.width - draw_width) // 2
        origin_y = map_rect.y + (map_rect.height - draw_height) // 2

        composite_surface = pygame.Surface((draw_width, draw_height), pygame.SRCALPHA)
        map_surface = pygame.transform.smoothscale(raw_map_surface, (draw_width, draw_height))
        map_surface = map_surface.copy()
        map_surface.fill((55, 55, 55, 0), special_flags=pygame.BLEND_RGB_ADD)
        composite_surface.blit(map_surface, (0, 0))

        tile_width = draw_width / level.width
        tile_height = draw_height / level.height
        fog_surface = pygame.Surface((draw_width, draw_height), pygame.SRCALPHA)
        for row in range(level.height):
            for col in range(level.width):
                if not visited[row][col]:
                    fog_rect = pygame.Rect(
                        int(col * tile_width),
                        int(row * tile_height),
                        max(1, int((col + 1) * tile_width) - int(col * tile_width)),
                        max(1, int((row + 1) * tile_height) - int(row * tile_height)),
                    )
                    fog_surface.fill((0, 0, 0, 255), fog_rect)

        composite_surface.blit(fog_surface, (0, 0))
        mask_surface = pygame.Surface((draw_width, draw_height), pygame.SRCALPHA)
        pygame.draw.rect(mask_surface, (255, 255, 255, 255), mask_surface.get_rect(), border_radius=18)
        composite_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.app.screen.blit(composite_surface, (origin_x, origin_y))
        self._draw_player_marker(origin_x, origin_y, draw_width, draw_height)

        level_name = self.game_scene._localized_level_name()
        area_name = self.small_font.render(level_name, True, COLORS["WHITE"])
        self.app.screen.blit(area_name, (map_rect.x + 12, map_rect.bottom - area_name.get_height() - 10))

    def _draw_player_marker(self, origin_x, origin_y, draw_width, draw_height):
        tile_x = int(self.player.get_center().x // self.game_scene.level.tile_size)
        tile_y = int(self.player.get_center().y // self.game_scene.level.tile_size)

        tile_width = draw_width / self.game_scene.level.width
        tile_height = draw_height / self.game_scene.level.height
        center_x = origin_x + tile_x * tile_width + tile_width / 2
        center_y = origin_y + tile_y * tile_height + tile_height / 2
        radius = max(4, int(min(tile_width, tile_height) / 3))

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
