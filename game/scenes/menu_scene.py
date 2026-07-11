import pygame

from game.localization import get_localizer
from game.scenes.base import Scene
from game.scenes.menu_background import AnimatedMenuBackground
from settings import COLORS


class MenuScene(Scene):
    def __init__(self, app):
        self.app = app
        self.app.audio.play_music("system_main_menu")
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 28)
        self.message = ""
        self.message_timer = 0.0
        self.buttons = []
        self._layout_size = None
        self.background = AnimatedMenuBackground(pan_seconds=20.0, blur_divisor=8, overlay_color=(10, 12, 18, 116))
        self._build_buttons()

    def _build_buttons(self):
        screen_width, screen_height = self.app.get_screen_size()
        button_width = 300
        button_height = 48
        gap = 14
        has_slots = self.app.save_manager.has_slots()
        labels = [
            (self.localizer.t("ui.menu.new_game"), self.start_game, False),
            (self.localizer.t("ui.menu.continue_game"), self.continue_game, not has_slots),
            (self.localizer.t("ui.menu.settings"), self.open_settings, False),
            (self.localizer.t("ui.menu.exit"), self.exit_game, False),
        ]

        title_gap = 72
        title_height = self.title_font.get_height()
        buttons_height = len(labels) * button_height + max(0, len(labels) - 1) * gap
        content_height = title_height + title_gap + buttons_height
        content_top = max(40, (screen_height - content_height) // 2)
        self.title_center_y = content_top + title_height // 2
        start_y = content_top + title_height + title_gap

        self.buttons = []
        for index, (label, action, disabled) in enumerate(labels):
            rect = pygame.Rect(
                (screen_width - button_width) // 2,
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
        self._layout_size = self.app.get_screen_size()

    def _ensure_layout(self):
        if self._layout_size != self.app.get_screen_size():
            self._build_buttons()
            self.background.recalculate()

    def on_language_changed(self):
        self._build_buttons()

    def set_message(self, text):
        self.message = text
        self.message_timer = 2.0

    def start_game(self):
        from game.scenes.save_slots_scene import SaveSlotsScene

        self.app.set_scene(SaveSlotsScene(self.app, self, mode="new"))

    def continue_game(self):
        from game.scenes.save_slots_scene import SaveSlotsScene

        self.app.set_scene(SaveSlotsScene(self.app, self, mode="continue"))

    def open_settings(self):
        from game.scenes.settings_scene import SettingsScene

        self.app.set_scene(SettingsScene(self.app, self))

    def show_author(self):
        self.set_message(self.localizer.t("ui.menu.author_message"))

    def exit_game(self):
        self.app.running = False

    def handle_events(self, events):
        self._ensure_layout()
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
        self.background.update(dt)
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0.0:
                self.message = ""

    def draw(self):
        self._ensure_layout()
        screen_width, screen_height = self.app.get_screen_size()
        self.background.draw(self.app.screen)

        title = self.title_font.render(self.localizer.t("ui.menu.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, title.get_rect(center=(screen_width // 2, self.title_center_y)))

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
                message.get_rect(center=(screen_width // 2, screen_height - 105)),
            )
