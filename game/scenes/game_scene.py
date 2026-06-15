import pygame

from game.core.camera import Camera
from game.core.vector import Vector2
from game.entities.player import Player
from game.objects import create_world_object
from game.scenes.base import Scene
from game.ui.hud import HUD
from game.world.collision import CollisionSystem
from game.world.level import load_level
from game.world.tilemap import TileMap
from settings import COLORS, SCREEN_WIDTH


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
        self.world_objects = self._load_world_objects()
        self.collision_system.set_objects(self.world_objects)

        world_width = self.tilemap.width * self.tilemap.tile_size
        world_height = self.tilemap.height * self.tilemap.tile_size
        self.camera = Camera(world_width, world_height)
        self.hud = HUD()
        self.info_font = pygame.font.Font(None, 28)
        self.interaction_font = pygame.font.Font(None, 30)
        self.last_interaction_message = ""
        self.last_interaction_timer = 0.0
        self.current_interaction_target = None

    def _load_world_objects(self):
        world_objects = []
        for raw_object in self.level.objects:
            world_object = create_world_object(raw_object, self.level.tile_size)
            if world_object is not None:
                world_objects.append(world_object)
        return world_objects

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
                elif event.key == pygame.K_e:
                    self.try_interact()
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

    def try_interact(self):
        target = self._find_interaction_target()
        if target is None:
            self.last_interaction_message = "Рядом нет объекта для взаимодействия"
            self.last_interaction_timer = 1.0
            return False

        return target.interact(self.player, self)

    def _find_interaction_target(self):
        player_zone = self.player.get_interaction_rect()
        candidates = []
        for world_object in self.world_objects:
            if not world_object.is_interactable:
                continue

            object_zone = world_object.get_interaction_rect()
            if _rects_intersect(player_zone, object_zone):
                candidates.append(world_object)

        if not candidates:
            return None

        player_center = self.player.get_center()
        return min(candidates, key=lambda obj: _distance_squared(player_center, obj.get_center()))

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self)
        self.camera.update(self.player)
        self.current_interaction_target = self._find_interaction_target()
        if self.last_interaction_timer > 0:
            self.last_interaction_timer = max(0.0, self.last_interaction_timer - dt)
            if self.last_interaction_timer == 0.0:
                self.last_interaction_message = ""

    def draw(self):
        self.app.screen.fill(COLORS["BLACK"])
        self.tilemap.draw(self.app.screen, self.camera)
        for world_object in self.world_objects:
            world_object.draw(self.app.screen, self.camera)
        self.player.draw(self.app.screen, self.camera)
        self.hud.draw(self.app.screen, self.player)
        if self.current_interaction_target is not None:
            self._draw_interaction_prompt(self.current_interaction_target)
        if self.last_interaction_message:
            message = self.info_font.render(self.last_interaction_message, True, COLORS["WHITE"])
            self.app.screen.blit(
                message,
                message.get_rect(center=(SCREEN_WIDTH // 2, 24)),
            )

    def _draw_interaction_prompt(self, world_object):
        prompt_text = self.interaction_font.render("E", True, COLORS["WHITE"])
        padding_x = 10
        padding_y = 6
        bubble_width = prompt_text.get_width() + padding_x * 2
        bubble_height = prompt_text.get_height() + padding_y * 2

        bubble_x = (
            world_object.position.x
            + world_object.width / 2
            - bubble_width / 2
            - self.camera.position.x
        )
        bubble_y = world_object.position.y - bubble_height - 10 - self.camera.position.y

        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
        pygame.draw.rect(
            self.app.screen,
            (30, 30, 36),
            bubble_rect,
            border_radius=8,
        )
        pygame.draw.rect(
            self.app.screen,
            COLORS["INTERACTABLE_ACTIVE"],
            bubble_rect,
            width=2,
            border_radius=8,
        )
        self.app.screen.blit(
            prompt_text,
            prompt_text.get_rect(center=bubble_rect.center),
        )


def _rects_intersect(rect_a, rect_b):
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b
    return (
        ax < bx + bw
        and ax + aw > bx
        and ay < by + bh
        and ay + ah > by
    )


def _distance_squared(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    return dx * dx + dy * dy
