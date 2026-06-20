import sys

import pygame

from game.localization import get_localizer
from game.scenes.menu_scene import MenuScene
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


class GameApp:
    def __init__(self):
        pygame.init()
        self.display_mode = "windowed"
        self.screen = None
        self._apply_display_mode()
        self.clock = pygame.time.Clock()
        self.running = True
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

    def _apply_display_mode(self):
        width, height = self._get_display_size_for_mode(self.display_mode)
        flags = 0
        if self.display_mode == "fullscreen":
            flags = pygame.FULLSCREEN
        elif self.display_mode == "borderless":
            flags = pygame.NOFRAME

        pygame.display.set_caption("Weales in the weeds RPG")
        self.screen = pygame.display.set_mode((width, height), flags)

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

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            if dt > 0.033:
                dt = 0.033

            events = pygame.event.get()
            self.scene.handle_events(events)
            self.scene.update(dt)
            self.scene.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()
