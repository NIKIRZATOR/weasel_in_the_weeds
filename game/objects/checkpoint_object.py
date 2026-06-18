import math

import pygame

from game.objects.world_object import WorldObject
from settings import COLORS


class CheckpointObject(WorldObject):
    def __init__(self, x, y, width, height, name="checkpoint_object", properties=None):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=COLORS["STONE"],
            is_solid=False,
            is_interactable=False,
            properties=properties,
        )
        self.is_checkpoint = True
        self.is_activated = False
        radius_tiles = float(self.properties.get("activation_radius_tiles", 1))
        self.activation_radius = max(0.0, radius_tiles * width)

    def can_activate(self, player):
        if self.is_activated:
            return False

        checkpoint_center = self.get_center()
        player_center = player.get_center()
        distance = math.hypot(
            player_center.x - checkpoint_center.x,
            player_center.y - checkpoint_center.y,
        )
        return distance <= self.activation_radius

    def activate(self, player, game_scene):
        if not self.can_activate(player):
            return False

        respawn_x = self.position.x + self.width
        respawn_y = self.position.y
        player.set_respawn_point(respawn_x, respawn_y)
        self.is_activated = True
        game_scene.last_interaction_message = f"Checkpoint activated: {self.name}"
        game_scene.last_interaction_timer = 1.5
        return True

    def draw(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y

        points = [
            (screen_x + self.width / 2, screen_y),
            (screen_x, screen_y + self.height),
            (screen_x + self.width, screen_y + self.height),
        ]

        pygame.draw.polygon(screen, COLORS["STONE"], points)
        border_color = COLORS["UI_SLOT_SELECTED"] if self.is_activated else COLORS["BLACK"]
        border_width = 4 if self.is_activated else 2
        pygame.draw.polygon(screen, border_color, points, width=border_width)
        self.draw_debug(screen, camera)
