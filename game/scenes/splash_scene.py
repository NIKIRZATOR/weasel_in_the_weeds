import pygame

from game.scenes.base import Scene
from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH


class SplashScene(Scene):
    def __init__(
        self,
        app,
        next_scene_factory,
        title="Загрузка...",
        duration=2.0,
        background=(15, 15, 25),
    ):
        self.app = app
        self.next_scene_factory = next_scene_factory
        self.title = title
        self.duration = duration
        self.background = background
        self.elapsed = 0.0
        self.font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 28)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.app.set_scene(self.next_scene_factory())

    def draw(self):
        self.app.screen.fill(self.background)

        title = self.font.render(self.title, True, COLORS["WHITE"])
        self.app.screen.blit(
            title,
            title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)),
        )

        progress = min(1.0, self.elapsed / self.duration)
        bar_width = 420
        bar_height = 28
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = SCREEN_HEIGHT // 2

        pygame.draw.rect(
            self.app.screen,
            (60, 60, 80),
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=8,
        )
        pygame.draw.rect(
            self.app.screen,
            (80, 180, 255),
            (bar_x, bar_y, int(bar_width * progress), bar_height),
            border_radius=8,
        )
        pygame.draw.rect(
            self.app.screen,
            COLORS["WHITE"],
            (bar_x, bar_y, bar_width, bar_height),
            width=2,
            border_radius=8,
        )

        percent = self.small_font.render(f"{int(progress * 100)}%", True, COLORS["WHITE"])
        self.app.screen.blit(
            percent,
            percent.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height + 28)),
        )
