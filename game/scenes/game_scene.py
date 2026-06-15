import pygame

from game.core.camera import Camera
from game.core.vector import Vector2
from game.entities.player import Player
from game.scenes.base import Scene
from game.ui.hud import HUD
from game.world.collision import CollisionSystem
from game.world.level import load_level
from game.world.tilemap import TileMap
from settings import COLORS


class GameScene(Scene):
    def __init__(self, app, level_path):
        self.app = app
        self.level = load_level(level_path)
        pygame.display.set_caption(f"Weales in the weeds RPG - {self.level.name}")

        self.tilemap = TileMap(
            self.level.ground_layer,
            self.level.obstacle_layer,
            tile_size=self.level.tile_size,
        )
        self.collision_system = CollisionSystem(self.tilemap)

        spawn_x, spawn_y = self.level.player_spawn
        spawn_world_x = self.level.tile_size * spawn_x
        spawn_world_y = self.level.tile_size * spawn_y
        self.player = Player(
            spawn_world_x,
            spawn_world_y,
            spawn_x=spawn_world_x,
            spawn_y=spawn_world_y,
        )

        world_width = self.tilemap.width * self.tilemap.tile_size
        world_height = self.tilemap.height * self.tilemap.tile_size
        self.camera = Camera(world_width, world_height)
        self.hud = HUD()

    def open_pause_menu(self):
        from game.scenes.pause_menu_scene import PauseMenuScene

        self.app.set_scene(PauseMenuScene(self.app, self))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.open_pause_menu()
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
                        self.player.try_jump(Vector2(dx, dy), self)

    def check_collision(self, x, y, entity, ignore_jump=False):
        return self.collision_system.check_collision(x, y, entity, ignore_jump)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self)
        self.camera.update(self.player)

    def draw(self):
        self.app.screen.fill(COLORS["BLACK"])
        self.tilemap.draw(self.app.screen, self.camera)
        self.player.draw(self.app.screen, self.camera)
        self.hud.draw(self.app.screen, self.player)
