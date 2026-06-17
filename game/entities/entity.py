import pygame

from game.core.vector import Vector2
from settings import COLORS, SHOW_HITBOXES, SHOW_INTERACTION_ZONES


class Entity:
    """Базовый класс для игровых объектов с визуальным размером и хитбоксом."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        hitbox_width=None,
        hitbox_height=None,
        hitbox_offset_x=0,
        hitbox_offset_y=0,
        interaction_width=None,
        interaction_height=None,
        interaction_offset_x=None,
        interaction_offset_y=None,
    ):
        self.position = Vector2(x, y)
        self.width = width
        self.height = height
        self.hitbox_width = width if hitbox_width is None else hitbox_width
        self.hitbox_height = height if hitbox_height is None else hitbox_height
        self.hitbox_offset_x = hitbox_offset_x
        self.hitbox_offset_y = hitbox_offset_y
        self.interaction_width = (
            self.hitbox_width if interaction_width is None else interaction_width
        )
        self.interaction_height = (
            self.hitbox_height if interaction_height is None else interaction_height
        )
        self.interaction_offset_x = (
            self.hitbox_offset_x
            if interaction_offset_x is None
            else interaction_offset_x
        )
        self.interaction_offset_y = (
            self.hitbox_offset_y
            if interaction_offset_y is None
            else interaction_offset_y
        )
        self.velocity = Vector2(0, 0)

    def get_rect(self):
        """Возвращает визуальный прямоугольник сущности."""
        return (self.position.x, self.position.y, self.width, self.height)

    def get_hitbox_at(self, x, y):
        """Возвращает хитбокс сущности в указанной позиции."""
        return (
            x + self.hitbox_offset_x,
            y + self.hitbox_offset_y,
            self.hitbox_width,
            self.hitbox_height,
        )

    def get_hitbox_rect(self):
        return self.get_hitbox_at(self.position.x, self.position.y)

    def get_interaction_at(self, x, y):
        """Возвращает зону взаимодействия сущности в указанной позиции."""
        return (
            x + self.interaction_offset_x,
            y + self.interaction_offset_y,
            self.interaction_width,
            self.interaction_height,
        )

    def get_interaction_rect(self):
        return self.get_interaction_at(self.position.x, self.position.y)

    def get_center(self):
        """Возвращает центр физического хитбокса."""
        hitbox_x, hitbox_y, hitbox_width, hitbox_height = self.get_hitbox_rect()
        return Vector2(
            hitbox_x + hitbox_width / 2,
            hitbox_y + hitbox_height / 2,
        )

    def update(self, dt):
        pass

    def draw(self, screen, camera):
        pass

    def draw_debug(self, screen, camera):
        if SHOW_HITBOXES:
            hitbox_x, hitbox_y, hitbox_width, hitbox_height = self.get_hitbox_rect()
            pygame.draw.rect(
                screen,
                COLORS["HITBOX"],
                (
                    (hitbox_x - camera.position.x) * camera.zoom,
                    (hitbox_y - camera.position.y) * camera.zoom,
                    hitbox_width * camera.zoom,
                    hitbox_height * camera.zoom,
                ),
                max(1, int(2 * camera.zoom)),
            )

        if SHOW_INTERACTION_ZONES:
            zone_x, zone_y, zone_width, zone_height = self.get_interaction_rect()
            pygame.draw.rect(
                screen,
                COLORS["INTERACTION_ZONE"],
                (
                    (zone_x - camera.position.x) * camera.zoom,
                    (zone_y - camera.position.y) * camera.zoom,
                    zone_width * camera.zoom,
                    zone_height * camera.zoom,
                ),
                max(1, int(camera.zoom)),
            )
