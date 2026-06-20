import pygame

from game.objects.world_object import WorldObject
from settings import COLORS


class GrassHideZone(WorldObject):
    def __init__(self, x, y, width, height, name="grass_hide_zone", properties=None):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=COLORS["GRASS"],
            is_solid=False,
            is_interactable=False,
            properties=properties,
        )
        self.is_grass_hide_zone = True
        self.concealment = bool(self.properties.get("concealment", True))
        self.slow_multiplier = float(self.properties.get("slow_multiplier", 1.0))
        self.required_crouch = bool(self.properties.get("required_crouch", False))

    def can_hide(self, player):
        if not self.concealment:
            return False
        return True

    def draw(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        label_rect = pygame.Rect(screen_x, screen_y, self.width, self.height)

        points = [
            (screen_x + self.width / 2, screen_y),
            (screen_x, screen_y + self.height),
            (screen_x + self.width, screen_y + self.height),
        ]

        pygame.draw.polygon(screen, COLORS["GRASS"], points)
        pygame.draw.polygon(screen, COLORS["UI_SLOT_SELECTED"], points, width=3)
        self.draw_name_label(screen, label_rect)
        self.draw_debug(screen, camera)
