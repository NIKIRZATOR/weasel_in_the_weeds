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
        collision_circle_radius=None,
        collision_circle_offset_x=None,
        collision_circle_offset_y=None,
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
        self.collision_circle_radius = collision_circle_radius
        self.collision_circle_offset_x = (
            self.hitbox_offset_x + self.hitbox_width / 2
            if collision_circle_offset_x is None
            else collision_circle_offset_x
        )
        self.collision_circle_offset_y = (
            self.hitbox_offset_y + self.hitbox_height / 2
            if collision_circle_offset_y is None
            else collision_circle_offset_y
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

    def has_collision_circle(self):
        return self.collision_circle_radius is not None

    def get_collision_circle_at(self, x, y):
        if self.collision_circle_radius is None:
            return None
        return (
            x + self.collision_circle_offset_x,
            y + self.collision_circle_offset_y,
            self.collision_circle_radius,
        )

    def get_collision_circle(self):
        return self.get_collision_circle_at(self.position.x, self.position.y)

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
            if self.has_collision_circle():
                center_x, center_y, radius = self.get_collision_circle()
                pygame.draw.circle(
                    screen,
                    COLORS["HITBOX"],
                    (int(center_x - camera.position.x), int(center_y - camera.position.y)),
                    int(radius),
                    2,
                )
            else:
                hitbox_x, hitbox_y, hitbox_width, hitbox_height = self.get_hitbox_rect()
                pygame.draw.rect(
                    screen,
                    COLORS["HITBOX"],
                    (
                        hitbox_x - camera.position.x,
                        hitbox_y - camera.position.y,
                        hitbox_width,
                        hitbox_height,
                    ),
                    2,
                )

        if SHOW_INTERACTION_ZONES:
            zone_x, zone_y, zone_width, zone_height = self.get_interaction_rect()
            pygame.draw.rect(
                screen,
                COLORS["INTERACTION_ZONE"],
                (
                    zone_x - camera.position.x,
                    zone_y - camera.position.y,
                    zone_width,
                    zone_height,
                ),
                1,
            )
