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
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        pygame.draw.rect(
            screen,
            self.color,
            (screen_x, screen_y, self.width, self.height),
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            COLORS["BLACK"],
            (screen_x, screen_y, self.width, self.height),
            width=2,
            border_radius=6,
        )
        self.draw_debug(screen, camera)
