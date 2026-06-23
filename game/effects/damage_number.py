from game.core.vector import Vector2
from settings import COLORS


DAMAGE_NUMBER_DURATION = 0.75
DAMAGE_NUMBER_RISE_SPEED = 52


class DamageNumber:
    def __init__(self, text, x, y):
        self.text = text
        self.position = Vector2(x, y)
        self.age = 0.0
        self.duration = DAMAGE_NUMBER_DURATION
        self.is_dead = False

    def update(self, dt):
        self.age += dt
        self.position.y -= DAMAGE_NUMBER_RISE_SPEED * dt
        if self.age >= self.duration:
            self.is_dead = True

    def draw(self, screen, camera, font):
        progress = min(1.0, self.age / self.duration)
        alpha = int(255 * (1.0 - progress))
        scale_offset = -8 * progress
        text_surface = font.render(self.text, True, (255, 235, 120))
        outline_surface = font.render(self.text, True, COLORS["BLACK"])
        text_surface.set_alpha(alpha)
        outline_surface.set_alpha(alpha)

        x = self.position.x - camera.position.x
        y = self.position.y - camera.position.y + scale_offset
        rect = text_surface.get_rect(center=(x, y))
        for offset_x, offset_y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            screen.blit(outline_surface, rect.move(offset_x, offset_y))
        screen.blit(text_surface, rect)
