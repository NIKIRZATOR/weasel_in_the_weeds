import pygame

from game.scenes.base import Scene
from settings import COLORS, LEVELS_DIR, SCREEN_HEIGHT, SCREEN_WIDTH


class MenuScene(Scene):
    def __init__(self, app):
        self.app = app
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 28)
        self.message = ""
        self.message_timer = 0.0
        self.buttons = []
        self._build_buttons()

    def _build_buttons(self):
        button_width = 300
        button_height = 48
        start_y = 210
        gap = 14
        labels = [
            ("Новая игра", self.start_game, False),
            ("Продолжить игру", None, True),
            #("Выбрать сохранение", None, True),
            ("Настройки", self.show_coming_soon, False),
            ("Об авторе", self.show_author, False),
            ("Выход", self.exit_game, False),
        ]

        self.buttons = []
        for index, (label, action, disabled) in enumerate(labels):
            rect = pygame.Rect(
                (SCREEN_WIDTH - button_width) // 2,
                start_y + index * (button_height + gap),
                button_width,
                button_height,
            )
            self.buttons.append(
                {
                    "rect": rect,
                    "label": label,
                    "action": action,
                    "disabled": disabled,
                }
            )

    def set_message(self, text):
        self.message = text
        self.message_timer = 2.0

    def start_game(self):
        from game.scenes.game_scene import GameScene
        from game.scenes.splash_scene import SplashScene

        self.app.set_scene(
            SplashScene(
                self.app,
                lambda: GameScene(self.app, LEVELS_DIR / "level_01.json"),
                title="Новая игра...",
            )
        )

    def show_coming_soon(self):
        self.set_message("Раздел в разработке")

    def show_author(self):
        self.set_message("Автор: проект Weales in the weeds")

    def exit_game(self):
        self.app.running = False

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.app.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.start_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    if not button["disabled"] and button["rect"].collidepoint(mouse_pos):
                        button["action"]()
                        break

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0.0:
                self.message = ""

    def draw(self):
        self.app.screen.fill((18, 18, 26))

        title = self.title_font.render("Weales in the weeds", True, COLORS["WHITE"])
        self.app.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 110)))

        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            rect = button["rect"]
            disabled = button["disabled"]
            hovered = rect.collidepoint(mouse_pos)

            fill = (55, 55, 65)
            border = (100, 100, 120)
            text_color = (140, 140, 140) if disabled else COLORS["WHITE"]
            if hovered and not disabled:
                fill = (75, 75, 95)
                border = (120, 180, 255)

            pygame.draw.rect(self.app.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

            label = self.button_font.render(button["label"], True, text_color)
            self.app.screen.blit(label, label.get_rect(center=rect.center))

        if self.message:
            message = self.info_font.render(self.message, True, (255, 220, 120))
            self.app.screen.blit(
                message,
                message.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 105)),
            )
