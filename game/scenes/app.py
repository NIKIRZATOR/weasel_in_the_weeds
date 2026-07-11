import sys

import pygame

from game.core.assets import load_image
from game.localization import get_localizer
from game.save_system import SaveManager
from game.scenes.menu_scene import MenuScene
from settings import ASSETS_DIR, LEVELS_DIR
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


FULLSCREEN_WORLD_ZOOM = 2


class GameApp:
    def __init__(self):
        pygame.init()
        self.display_mode = "windowed"
        self.show_fps = True
        self.screen = None
        self._system_background_cache = {}
        self._cursor_surface = None
        self._apply_display_mode()
        self._load_system_cursor()
        self.clock = pygame.time.Clock()
        self.current_fps = 0.0
        self.running = True
        self.save_manager = SaveManager()
        self.scene = MenuScene(self)

    def set_scene(self, scene):
        self.scene = scene

    def set_display_mode(self, mode):
        if mode not in {"windowed", "fullscreen", "borderless"}:
            return False
        if self.display_mode == mode:
            return True
        self.display_mode = mode
        self._apply_display_mode()
        return True

    def set_language(self, language):
        localizer = get_localizer()
        if language not in localizer.available_languages():
            return False
        if localizer.get_language() == language:
            return True

        localizer.set_language(language)
        if self.scene is not None:
            self.scene.on_language_changed()
        return True

    def set_show_fps(self, value):
        self.show_fps = bool(value)
        return True

    def _apply_display_mode(self):
        width, height = self._get_display_size_for_mode(self.display_mode)
        flags = 0
        if self.display_mode == "fullscreen":
            flags = pygame.FULLSCREEN
        elif self.display_mode == "borderless":
            flags = pygame.NOFRAME

        pygame.display.set_caption("Weales in the weeds RPG")
        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.mouse.set_visible(self._cursor_surface is None)

    def _load_system_cursor(self):
        self._cursor_surface = load_image(ASSETS_DIR / "system" / "mouse.png")
        pygame.mouse.set_visible(self._cursor_surface is None)

    def draw_system_background(self, name, rect, border_radius=0, dim_alpha=72):
        source = self._get_system_background(name)
        if source is None:
            return False

        background = pygame.transform.smoothscale(source, rect.size)
        if dim_alpha > 0:
            dim_overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            dim_overlay.fill((18, 20, 26, dim_alpha))
            background.blit(dim_overlay, (0, 0))

        if border_radius > 0:
            mask = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=border_radius)
            background.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.screen.blit(background, rect.topleft)
        return True

    def draw_translucent_panel(self, rect, color, alpha=128, border_radius=0):
        panel_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel_color = (*color[:3], max(0, min(255, int(alpha))))
        pygame.draw.rect(panel_surface, panel_color, panel_surface.get_rect(), border_radius=border_radius)
        self.screen.blit(panel_surface, rect.topleft)

    def _get_system_background(self, name):
        if name not in self._system_background_cache:
            self._system_background_cache[name] = load_image(ASSETS_DIR / "system" / f"{name}.png")
        return self._system_background_cache[name]

    def draw_cursor(self):
        if self._cursor_surface is None:
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        cursor_rect = self._cursor_surface.get_rect(center=(mouse_x, mouse_y))
        self.screen.blit(self._cursor_surface, cursor_rect.topleft)

    def _get_display_size_for_mode(self, mode):
        if mode == "windowed":
            return SCREEN_WIDTH, SCREEN_HEIGHT

        desktop_sizes = pygame.display.get_desktop_sizes()
        if desktop_sizes:
            return desktop_sizes[0]

        info = pygame.display.Info()
        return info.current_w, info.current_h

    def get_screen_size(self):
        return self.screen.get_size()

    def get_world_zoom(self):
        if self.display_mode == "fullscreen":
            return FULLSCREEN_WORLD_ZOOM
        return 1.0

    def get_world_render_size(self):
        screen_width, screen_height = self.get_screen_size()
        zoom = max(0.1, float(self.get_world_zoom()))
        return (
            max(1, int(round(screen_width / zoom))),
            max(1, int(round(screen_height / zoom))),
        )

    def start_new_game(self, slot_id):
        from game.scenes.game_scene import GameScene
        from game.scenes.splash_scene import SplashScene

        if not self.save_manager.set_active_slot(slot_id):
            return False
        self.set_scene(
            SplashScene(
                self,
                lambda: GameScene(self, LEVELS_DIR / "level_01"),
                title=get_localizer().t("ui.menu.new_game_loading"),
            )
        )
        return True

    def continue_game(self, slot_id):
        from game.scenes.game_scene import GameScene
        from game.scenes.splash_scene import SplashScene

        save_data = self.save_manager.load_slot_data(slot_id)
        if save_data is None:
            return False
        if not self.save_manager.set_active_slot(slot_id):
            return False

        level_key = save_data.get("current_level") or "level_01"
        self.set_scene(
            SplashScene(
                self,
                lambda: GameScene(self, LEVELS_DIR / level_key, save_data=save_data),
                title=get_localizer().t("ui.menu.continue_game"),
            )
        )
        return True

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.current_fps = self.clock.get_fps()
            if dt > 0.033:
                dt = 0.033

            events = pygame.event.get()
            self.scene.handle_events(events)
            self.scene.update(dt)
            self.scene.draw()
            self.draw_cursor()
            pygame.display.flip()

        pygame.quit()
        sys.exit()
