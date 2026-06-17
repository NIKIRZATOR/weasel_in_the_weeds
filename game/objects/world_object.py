import pygame

from game.entities.entity import Entity
from settings import COLORS


class WorldObject(Entity):
    """Базовый объект мира, загружаемый из уровня."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="object",
        color=None,
        is_solid=False,
        is_interactable=False,
        hitbox_width=None,
        hitbox_height=None,
        hitbox_offset_x=0,
        hitbox_offset_y=0,
        interaction_width=None,
        interaction_height=None,
        interaction_offset_x=None,
        interaction_offset_y=None,
        properties=None,
    ):
        super().__init__(
            x,
            y,
            width,
            height,
            hitbox_width=hitbox_width,
            hitbox_height=hitbox_height,
            hitbox_offset_x=hitbox_offset_x,
            hitbox_offset_y=hitbox_offset_y,
            interaction_width=interaction_width,
            interaction_height=interaction_height,
            interaction_offset_x=interaction_offset_x,
            interaction_offset_y=interaction_offset_y,
        )
        self.name = name
        self.color = COLORS["SOLID_OBJECT"] if color is None else color
        self.is_solid = is_solid
        self.is_interactable = is_interactable
        self.properties = {} if properties is None else properties
        self.is_active = False

    def interact(self, player, game_scene):
        return False

    def draw(self, screen, camera):
        screen_x = (self.position.x - camera.position.x) * camera.zoom
        screen_y = (self.position.y - camera.position.y) * camera.zoom
        width = self.width * camera.zoom
        height = self.height * camera.zoom
        border_radius = max(2, int(6 * camera.zoom))
        pygame.draw.rect(
            screen,
            self.color,
            (screen_x, screen_y, width, height),
            border_radius=border_radius,
        )
        pygame.draw.rect(
            screen,
            COLORS["BLACK"],
            (screen_x, screen_y, width, height),
            width=max(1, int(2 * camera.zoom)),
            border_radius=border_radius,
        )
        self.draw_debug(screen, camera)
