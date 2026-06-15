import sys

import pygame

from game.scenes.menu_scene import MenuScene
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


class GameApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Weales in the weeds RPG")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = MenuScene(self)

    def set_scene(self, scene):
        self.scene = scene

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
