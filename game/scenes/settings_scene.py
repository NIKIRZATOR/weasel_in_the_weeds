import pygame

from game.localization import get_localizer
from game.scenes.base import Scene
from settings import COLORS


class SettingsScene(Scene):
    def __init__(self, app, previous_scene, overlay_scene=None):
        self.app = app
        self.previous_scene = previous_scene
        self.overlay_scene = overlay_scene
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 64)
        self.section_font = pygame.font.Font(None, 34)
        self.button_font = pygame.font.Font(None, 30)
        self.info_font = pygame.font.Font(None, 24)
        self._layout_size = None
        self._build_buttons()

    def _build_buttons(self):
        screen_width, screen_height = self.app.get_screen_size()
        mode_options = [
            (self.localizer.t("ui.settings.mode_windowed"), "windowed"),
            (self.localizer.t("ui.settings.mode_fullscreen"), "fullscreen"),
            (self.localizer.t("ui.settings.mode_borderless"), "borderless"),
        ]
        language_options = [
            (self.localizer.t("ui.settings.language_ru"), "ru"),
            (self.localizer.t("ui.settings.language_en"), "en"),
        ]

        panel_width = min(760, screen_width - 48)
        panel_height = min(500, screen_height - 48)
        self.panel_rect = pygame.Rect(
            (screen_width - panel_width) // 2,
            (screen_height - panel_height) // 2,
            panel_width,
            panel_height,
        )

        self.title_y = self.panel_rect.y + 42
        content_left = self.panel_rect.x + 28
        content_right = self.panel_rect.right - 28
        content_width = content_right - content_left
        label_width = min(220, max(150, int(content_width * 0.32)))
        options_gap = 12
        options_width = content_width - label_width - options_gap
        row_height = 56

        self.mode_row_rect = pygame.Rect(content_left, self.panel_rect.y + 122, content_width, row_height)
        self.language_row_rect = pygame.Rect(content_left, self.mode_row_rect.bottom + 26, content_width, row_height)
        self.fps_row_rect = pygame.Rect(content_left, self.language_row_rect.bottom + 26, content_width, row_height)

        self.mode_buttons = self._build_option_row(
            self.mode_row_rect,
            mode_options,
            key_name="mode",
            label_width=label_width,
            options_width=options_width,
        )
        self.language_buttons = self._build_option_row(
            self.language_row_rect,
            language_options,
            key_name="language",
            label_width=label_width,
            options_width=options_width,
        )
        fps_options = [
            (self.localizer.t("ui.settings.option_on"), True),
            (self.localizer.t("ui.settings.option_off"), False),
        ]
        self.fps_buttons = self._build_option_row(
            self.fps_row_rect,
            fps_options,
            key_name="fps",
            label_width=label_width,
            options_width=options_width,
        )

        back_width = min(220, self.panel_rect.width - 56)
        self.back_button = pygame.Rect(
            self.panel_rect.centerx - back_width // 2,
            self.fps_row_rect.bottom + 42,
            back_width,
            44,
        )
        self.footer_y = self.back_button.bottom + 26
        self._layout_size = self.app.get_screen_size()

    def _build_option_row(self, row_rect, options, key_name, label_width, options_width):
        button_gap = 10
        count = max(1, len(options))
        button_width = max(96, (options_width - button_gap * (count - 1)) // count)
        button_height = 44
        buttons_left = row_rect.right - options_width
        button_top = row_rect.y + (row_rect.height - button_height) // 2

        buttons = []
        for index, (label, value) in enumerate(options):
            rect = pygame.Rect(
                buttons_left + index * (button_width + button_gap),
                button_top,
                button_width,
                button_height,
            )
            buttons.append({"rect": rect, "label": label, key_name: value})
        return buttons

    def _ensure_layout(self):
        if self._layout_size != self.app.get_screen_size():
            self._build_buttons()

    def on_language_changed(self):
        self._build_buttons()
        if self.previous_scene is not None:
            self.previous_scene.on_language_changed()
        if self.overlay_scene is not None and self.overlay_scene is not self.previous_scene:
            self.overlay_scene.on_language_changed()

    def go_back(self):
        self.app.set_scene(self.previous_scene)

    def handle_events(self, events):
        self._ensure_layout()
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.go_back()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.mode_buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        self.app.set_display_mode(button["mode"])
                        return
                for button in self.language_buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        self.app.set_language(button["language"])
                        self._build_buttons()
                        return
                for button in self.fps_buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        self.app.set_show_fps(button["fps"])
                        return
                if self.back_button.collidepoint(mouse_pos):
                    self.go_back()

    def update(self, dt):
        return None

    def draw(self):
        self._ensure_layout()
        screen_width, screen_height = self.app.get_screen_size()
        if self.overlay_scene is not None:
            self.overlay_scene.draw()
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 165))
            self.app.screen.blit(overlay, (0, 0))
        else:
            self.app.screen.fill((18, 18, 26))

        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.panel_rect, border_radius=16)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.panel_rect, width=2, border_radius=16)

        title = self.title_font.render(self.localizer.t("ui.settings.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, title.get_rect(center=(screen_width // 2, self.title_y)))

        mouse_pos = pygame.mouse.get_pos()
        self._draw_row_label(self.mode_row_rect, self.localizer.t("ui.settings.window_mode"))
        for button in self.mode_buttons:
            rect = button["rect"]
            hovered = rect.collidepoint(mouse_pos)
            active = self.app.display_mode == button["mode"]

            fill = (55, 55, 65)
            border = (100, 100, 120)
            if active:
                fill = (64, 90, 120)
                border = COLORS["UI_SLOT_SELECTED"]
            elif hovered:
                fill = (75, 75, 95)
                border = (120, 180, 255)

            pygame.draw.rect(self.app.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

            label = self.button_font.render(button["label"], True, COLORS["WHITE"])
            self.app.screen.blit(label, label.get_rect(center=rect.center))

        current_language = self.localizer.get_language()
        self._draw_row_label(self.language_row_rect, self.localizer.t("ui.settings.language"))
        for button in self.language_buttons:
            rect = button["rect"]
            hovered = rect.collidepoint(mouse_pos)
            active = current_language == button["language"]

            fill = (55, 55, 65)
            border = (100, 100, 120)
            if active:
                fill = (64, 90, 120)
                border = COLORS["UI_SLOT_SELECTED"]
            elif hovered:
                fill = (75, 75, 95)
                border = (120, 180, 255)

            pygame.draw.rect(self.app.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

            label = self.button_font.render(button["label"], True, COLORS["WHITE"])
            self.app.screen.blit(label, label.get_rect(center=rect.center))

        self._draw_row_label(self.fps_row_rect, self.localizer.t("ui.settings.show_fps"))
        for button in self.fps_buttons:
            rect = button["rect"]
            hovered = rect.collidepoint(mouse_pos)
            active = self.app.show_fps == button["fps"]

            fill = (55, 55, 65)
            border = (100, 100, 120)
            if active:
                fill = (64, 90, 120)
                border = COLORS["UI_SLOT_SELECTED"]
            elif hovered:
                fill = (75, 75, 95)
                border = (120, 180, 255)

            pygame.draw.rect(self.app.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

            label = self.button_font.render(button["label"], True, COLORS["WHITE"])
            self.app.screen.blit(label, label.get_rect(center=rect.center))

        back_hovered = self.back_button.collidepoint(mouse_pos)
        back_fill = (55, 55, 65) if not back_hovered else (75, 75, 95)
        back_border = (100, 100, 120) if not back_hovered else (120, 180, 255)
        pygame.draw.rect(self.app.screen, back_fill, self.back_button, border_radius=8)
        pygame.draw.rect(self.app.screen, back_border, self.back_button, width=2, border_radius=8)

        back_label = self.button_font.render(self.localizer.t("ui.settings.back"), True, COLORS["WHITE"])
        self.app.screen.blit(back_label, back_label.get_rect(center=self.back_button.center))

        current_label = self.info_font.render(
            self.localizer.t("ui.settings.current_mode", mode=self._mode_title(self.app.display_mode)),
            True,
            COLORS["UI_TEXT_DIM"],
        )
        self.app.screen.blit(
            current_label,
            current_label.get_rect(center=(screen_width // 2, self.footer_y)),
        )

        hint_text = self.localizer.t(
            "ui.settings.language_hint",
            language=self.localizer.t(f"ui.settings.language_{current_language}"),
        )
        hint = self.info_font.render(hint_text, True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(hint, hint.get_rect(center=(screen_width // 2, self.footer_y + 26)))

    def _mode_title(self, mode):
        titles = {
            "windowed": self.localizer.t("ui.settings.mode_windowed"),
            "fullscreen": self.localizer.t("ui.settings.mode_fullscreen"),
            "borderless": self.localizer.t("ui.settings.mode_borderless"),
        }
        return titles.get(mode, mode)

    def _draw_row_label(self, row_rect, text):
        label = self.section_font.render(text, True, COLORS["UI_TEXT_DIM"])
        label_rect = label.get_rect()
        label_rect.midleft = (row_rect.x + 4, row_rect.centery)
        self.app.screen.blit(label, label_rect)
