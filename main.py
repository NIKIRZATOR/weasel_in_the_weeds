import sys

import pygame

from game.core.camera import Camera
from game.core.vector import Vector2
from game.entities.player import Player
from game.ui.hud import HUD
from game.world.collision import CollisionSystem
from game.world.level import load_level
from game.world.tilemap import TileMap
from settings import COLORS, LEVELS_DIR, SCREEN_HEIGHT, SCREEN_WIDTH


class Game:

    def __init__(self, level_path):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.level = load_level(level_path)
        pygame.display.set_caption(f"Top-Down RPG - {self.level.name}")

        self.tilemap = TileMap(
            self.level.ground_layer,
            self.level.obstacle_layer,
            tile_size=self.level.tile_size,
        )
        self.collision_system = CollisionSystem(self.tilemap)

        spawn_x, spawn_y = self.level.player_spawn
        self.player = Player(
            self.level.tile_size * spawn_x,
            self.level.tile_size * spawn_y,
            spawn_x=self.level.tile_size * spawn_x,
            spawn_y=self.level.tile_size * spawn_y,
        )

        world_width = self.tilemap.width * self.tilemap.tile_size
        world_height = self.tilemap.height * self.tilemap.tile_size
        self.camera = Camera(world_width, world_height)
        self.hud = HUD()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_f:
                    self.player.attack()
                elif event.key == pygame.K_SPACE and not self.player.is_jumping:
                    keys = pygame.key.get_pressed()
                    dx = 0
                    dy = 0
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        dx = -1
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        dx = 1
                    if keys[pygame.K_UP] or keys[pygame.K_w]:
                        dy = -1
                    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                        dy = 1

                    if dx != 0 or dy != 0:
                        direction = Vector2(dx, dy)
                        self.player.try_jump(direction, self)

    def check_collision(self, x, y, entity, ignore_jump=False):
        return self.collision_system.check_collision(x, y, entity, ignore_jump)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self)
        self.camera.update(self.player)

    def draw(self):
        self.screen.fill(COLORS["BLACK"])
        self.tilemap.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        self.hud.draw(self.screen, self.player)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            if dt > 0.033:
                dt = 0.033

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game(LEVELS_DIR / "level_01.json")
    game.run()
