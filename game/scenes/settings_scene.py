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
        self.buttons = []
        self._layout_size = None
        self._build_buttons()

    def _build_buttons(self):
        screen_width, screen_height = self.app.get_screen_size()
        button_width = 340
        button_height = 50
        gap = 16
        options = [
            (self.localizer.t("ui.settings.mode_windowed"), "windowed"),
            (self.localizer.t("ui.settings.mode_fullscreen"), "fullscreen"),
            (self.localizer.t("ui.settings.mode_borderless"), "borderless"),
        ]

        title_gap = 54
        title_height = self.title_font.get_height()
        subtitle_height = self.section_font.get_height()
        buttons_height = len(options) * button_height + max(0, len(options) - 1) * gap
        back_height = 48
        content_height = title_height + title_gap + subtitle_height + 28 + buttons_height + 36 + back_height
        content_top = max(36, (screen_height - content_height) // 2)

        self.title_center_y = content_top + title_height // 2
        self.subtitle_center_y = content_top + title_height + title_gap + subtitle_height // 2
        start_y = content_top + title_height + title_gap + subtitle_height + 28

        self.buttons = []
        for index, (label, mode) in enumerate(options):
            rect = pygame.Rect(
                (screen_width - button_width) // 2,
                start_y + index * (button_height + gap),
                button_width,
                button_height,
            )
            self.buttons.append({"rect": rect, "label": label, "mode": mode})

        self.back_button = pygame.Rect((screen_width - 220) // 2, start_y + buttons_height + 36, 220, 48)
        self._layout_size = self.app.get_screen_size()

    def _ensure_layout(self):
        if self._layout_size != self.app.get_screen_size():
            self._build_buttons()

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
                for button in self.buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        self.app.set_display_mode(button["mode"])
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

        title = self.title_font.render(self.localizer.t("ui.settings.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, title.get_rect(center=(screen_width // 2, self.title_center_y)))

        subtitle = self.section_font.render(self.localizer.t("ui.settings.window_mode"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(subtitle, subtitle.get_rect(center=(screen_width // 2, self.subtitle_center_y)))

        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
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
            current_label.get_rect(center=(screen_width // 2, screen_height - 80)),
        )

        hint = self.info_font.render(self.localizer.t("ui.settings.close_hint"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(hint, hint.get_rect(center=(screen_width // 2, screen_height - 48)))

    def _mode_title(self, mode):
        titles = {
            "windowed": self.localizer.t("ui.settings.mode_windowed"),
            "fullscreen": self.localizer.t("ui.settings.mode_fullscreen"),
            "borderless": self.localizer.t("ui.settings.mode_borderless"),
        }
        return titles.get(mode, mode)
