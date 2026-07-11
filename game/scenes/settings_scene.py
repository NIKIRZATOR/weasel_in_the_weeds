import pygame

from game.localization import get_localizer
from game.scenes.base import Scene
from game.scenes.menu_background import AnimatedMenuBackground
from settings import COLORS


class SettingsScene(Scene):
    ROW_HEIGHT = 56
    ROW_GAP = 26

    def __init__(self, app, previous_scene, overlay_scene=None):
        self.app = app
        if overlay_scene is None:
            self.app.audio.play_music("system_main_menu")
        self.previous_scene = previous_scene
        self.overlay_scene = overlay_scene
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 64)
        self.section_font = pygame.font.Font(None, 34)
        self.button_font = pygame.font.Font(None, 30)
        self.info_font = pygame.font.Font(None, 24)
        self._layout_size = None
        self.background = AnimatedMenuBackground(pan_seconds=20.0, blur_divisor=8, overlay_color=(10, 12, 18, 132))
        self.scroll_offset = 0
        self.scroll_drag_active = False
        self.scroll_drag_offset_y = 0
        self.active_slider = None
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
        fps_options = [
            (self.localizer.t("ui.settings.option_on"), True),
            (self.localizer.t("ui.settings.option_off"), False),
        ]

        panel_width = min(760, screen_width - 48)
        panel_height = min(620, screen_height - 48)
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

        back_width = min(220, self.panel_rect.width - 56)
        self.back_button = pygame.Rect(
            self.panel_rect.centerx - back_width // 2,
            self.panel_rect.bottom - 68,
            back_width,
            44,
        )
        self.footer_primary_y = self.back_button.y - 42
        self.footer_secondary_y = self.back_button.y - 18

        viewport_top = self.panel_rect.y + 112
        viewport_bottom = self.footer_primary_y - 18
        scrollbar_width = 12
        self.content_viewport_rect = pygame.Rect(
            content_left,
            viewport_top,
            content_width - scrollbar_width - 10,
            max(120, viewport_bottom - viewport_top),
        )
        self.scrollbar_track_rect = pygame.Rect(
            self.content_viewport_rect.right + 10,
            self.content_viewport_rect.y,
            scrollbar_width,
            self.content_viewport_rect.height,
        )

        row_y = 0
        self.mode_row_rect = pygame.Rect(0, row_y, self.content_viewport_rect.width, self.ROW_HEIGHT)
        row_y += self.ROW_HEIGHT + self.ROW_GAP
        self.language_row_rect = pygame.Rect(0, row_y, self.content_viewport_rect.width, self.ROW_HEIGHT)
        row_y += self.ROW_HEIGHT + self.ROW_GAP
        self.fps_row_rect = pygame.Rect(0, row_y, self.content_viewport_rect.width, self.ROW_HEIGHT)
        row_y += self.ROW_HEIGHT + self.ROW_GAP
        self.music_volume_row_rect = pygame.Rect(0, row_y, self.content_viewport_rect.width, self.ROW_HEIGHT)
        row_y += self.ROW_HEIGHT + self.ROW_GAP
        self.sfx_volume_row_rect = pygame.Rect(0, row_y, self.content_viewport_rect.width, self.ROW_HEIGHT)
        row_y += self.ROW_HEIGHT
        self.content_height = row_y

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
        self.fps_buttons = self._build_option_row(
            self.fps_row_rect,
            fps_options,
            key_name="fps",
            label_width=label_width,
            options_width=options_width,
        )
        self.music_slider = self._build_slider_row(
            self.music_volume_row_rect,
            label_width=label_width,
            options_width=options_width,
        )
        self.sfx_slider = self._build_slider_row(
            self.sfx_volume_row_rect,
            label_width=label_width,
            options_width=options_width,
        )

        self._clamp_scroll()
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

    def _build_slider_row(self, row_rect, label_width, options_width):
        slider_width = max(150, options_width - 140)
        slider_height = 8
        slider_left = row_rect.right - options_width + 24
        track_rect = pygame.Rect(
            slider_left,
            row_rect.centery - slider_height // 2,
            slider_width,
            slider_height,
        )
        value_rect = pygame.Rect(track_rect.right + 12, row_rect.y, 60, row_rect.height)
        return {"track_rect": track_rect, "value_rect": value_rect}

    def _ensure_layout(self):
        if self._layout_size != self.app.get_screen_size():
            self._build_buttons()
            self.background.recalculate()

    def _max_scroll(self):
        return max(0, self.content_height - self.content_viewport_rect.height)

    def _clamp_scroll(self):
        self.scroll_offset = max(0, min(self.scroll_offset, self._max_scroll()))

    def _scroll(self, delta):
        self.scroll_offset += delta
        self._clamp_scroll()

    def _content_mouse_pos(self, mouse_pos):
        if not self.content_viewport_rect.collidepoint(mouse_pos):
            return None
        return (
            mouse_pos[0] - self.content_viewport_rect.x,
            mouse_pos[1] - self.content_viewport_rect.y + self.scroll_offset,
        )

    def _screen_rect_from_content(self, rect):
        return pygame.Rect(
            self.content_viewport_rect.x + rect.x,
            self.content_viewport_rect.y + rect.y - self.scroll_offset,
            rect.width,
            rect.height,
        )

    def _scrollbar_thumb_rect(self):
        if self.content_height <= self.content_viewport_rect.height:
            return self.scrollbar_track_rect.copy()
        track_rect = self.scrollbar_track_rect
        thumb_height = max(36, int(track_rect.height * (self.content_viewport_rect.height / self.content_height)))
        max_scroll = max(1, self._max_scroll())
        thumb_range = track_rect.height - thumb_height
        thumb_offset = int((self.scroll_offset / max_scroll) * thumb_range)
        return pygame.Rect(track_rect.x, track_rect.y + thumb_offset, track_rect.width, thumb_height)

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
                content_mouse_pos = self._content_mouse_pos(mouse_pos)
                if content_mouse_pos is not None:
                    for button in self.mode_buttons:
                        if button["rect"].collidepoint(content_mouse_pos):
                            self.app.set_display_mode(button["mode"])
                            return
                    for button in self.language_buttons:
                        if button["rect"].collidepoint(content_mouse_pos):
                            self.app.set_language(button["language"])
                            self._build_buttons()
                            return
                    for button in self.fps_buttons:
                        if button["rect"].collidepoint(content_mouse_pos):
                            self.app.set_show_fps(button["fps"])
                            return
                    if self.music_slider["track_rect"].inflate(0, 18).collidepoint(content_mouse_pos):
                        self.active_slider = "music"
                        self._update_slider_value("music", content_mouse_pos[0])
                        return
                    if self.sfx_slider["track_rect"].inflate(0, 18).collidepoint(content_mouse_pos):
                        self.active_slider = "sfx"
                        self._update_slider_value("sfx", content_mouse_pos[0])
                        return
                thumb_rect = self._scrollbar_thumb_rect()
                if thumb_rect.collidepoint(mouse_pos) and self._max_scroll() > 0:
                    self.scroll_drag_active = True
                    self.scroll_drag_offset_y = mouse_pos[1] - thumb_rect.y
                    return
                if self.scrollbar_track_rect.collidepoint(mouse_pos) and self._max_scroll() > 0:
                    self._jump_scroll_to(mouse_pos[1])
                    return
                if self.back_button.collidepoint(mouse_pos):
                    self.go_back()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.active_slider = None
                self.scroll_drag_active = False
            elif event.type == pygame.MOUSEMOTION:
                if self.active_slider is not None:
                    content_mouse_pos = self._content_mouse_pos(event.pos)
                    if content_mouse_pos is not None:
                        self._update_slider_value(self.active_slider, content_mouse_pos[0])
                elif self.scroll_drag_active:
                    self._drag_scroll_thumb(event.pos[1])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
                if self.content_viewport_rect.collidepoint(mouse_pos):
                    self._scroll(-40)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
                if self.content_viewport_rect.collidepoint(mouse_pos):
                    self._scroll(40)
            elif event.type == pygame.MOUSEWHEEL:
                if self.content_viewport_rect.collidepoint(mouse_pos):
                    self._scroll(-event.y * 40)

    def _jump_scroll_to(self, mouse_y):
        track_rect = self.scrollbar_track_rect
        thumb_rect = self._scrollbar_thumb_rect()
        thumb_center_y = mouse_y - thumb_rect.height // 2
        thumb_center_y = max(track_rect.y, min(track_rect.bottom - thumb_rect.height, thumb_center_y))
        self._set_scroll_from_thumb_top(thumb_center_y)

    def _drag_scroll_thumb(self, mouse_y):
        track_rect = self.scrollbar_track_rect
        thumb_rect = self._scrollbar_thumb_rect()
        thumb_top = mouse_y - self.scroll_drag_offset_y
        thumb_top = max(track_rect.y, min(track_rect.bottom - thumb_rect.height, thumb_top))
        self._set_scroll_from_thumb_top(thumb_top)

    def _set_scroll_from_thumb_top(self, thumb_top):
        track_rect = self.scrollbar_track_rect
        thumb_rect = self._scrollbar_thumb_rect()
        thumb_range = max(1, track_rect.height - thumb_rect.height)
        scroll_ratio = (thumb_top - track_rect.y) / thumb_range
        self.scroll_offset = int(round(scroll_ratio * self._max_scroll()))
        self._clamp_scroll()

    def update(self, dt):
        self.background.update(dt)
        return None

    def draw(self):
        self._ensure_layout()
        screen_width, screen_height = self.app.get_screen_size()
        self.background.draw(self.app.screen)

        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.panel_rect, border_radius=16)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.panel_rect, width=2, border_radius=16)

        title = self.title_font.render(self.localizer.t("ui.settings.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, title.get_rect(center=(screen_width // 2, self.title_y)))

        self._draw_content()
        self._draw_scrollbar()

        mouse_pos = pygame.mouse.get_pos()
        back_hovered = self.back_button.collidepoint(mouse_pos)
        back_fill = (55, 55, 65) if not back_hovered else (75, 75, 95)
        back_border = (100, 100, 120) if not back_hovered else (120, 180, 255)
        pygame.draw.rect(self.app.screen, back_fill, self.back_button, border_radius=8)
        pygame.draw.rect(self.app.screen, back_border, self.back_button, width=2, border_radius=8)

        back_label = self.button_font.render(self.localizer.t("ui.settings.back"), True, COLORS["WHITE"])
        self.app.screen.blit(back_label, back_label.get_rect(center=self.back_button.center))

        current_language = self.localizer.get_language()
        current_label = self.info_font.render(
            self.localizer.t("ui.settings.current_mode", mode=self._mode_title(self.app.display_mode)),
            True,
            COLORS["UI_TEXT_DIM"],
        )
        self.app.screen.blit(current_label, current_label.get_rect(center=(screen_width // 2, self.footer_primary_y)))

        hint_text = self.localizer.t(
            "ui.settings.language_hint",
            language=self.localizer.t(f"ui.settings.language_{current_language}"),
        )
        hint = self.info_font.render(hint_text, True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(hint, hint.get_rect(center=(screen_width // 2, self.footer_secondary_y)))

    def _draw_content(self):
        content_surface = pygame.Surface((self.content_viewport_rect.width, self.content_height), pygame.SRCALPHA)
        mouse_pos = pygame.mouse.get_pos()
        content_mouse_pos = self._content_mouse_pos(mouse_pos)

        self._draw_row_label(content_surface, self.mode_row_rect, self.localizer.t("ui.settings.window_mode"))
        for button in self.mode_buttons:
            self._draw_option_button(
                content_surface,
                button["rect"],
                button["label"],
                active=self.app.display_mode == button["mode"],
                hovered=content_mouse_pos is not None and button["rect"].collidepoint(content_mouse_pos),
            )

        current_language = self.localizer.get_language()
        self._draw_row_label(content_surface, self.language_row_rect, self.localizer.t("ui.settings.language"))
        for button in self.language_buttons:
            self._draw_option_button(
                content_surface,
                button["rect"],
                button["label"],
                active=current_language == button["language"],
                hovered=content_mouse_pos is not None and button["rect"].collidepoint(content_mouse_pos),
            )

        self._draw_row_label(content_surface, self.fps_row_rect, self.localizer.t("ui.settings.show_fps"))
        for button in self.fps_buttons:
            self._draw_option_button(
                content_surface,
                button["rect"],
                button["label"],
                active=self.app.show_fps == button["fps"],
                hovered=content_mouse_pos is not None and button["rect"].collidepoint(content_mouse_pos),
            )

        self._draw_row_label(content_surface, self.music_volume_row_rect, self.localizer.t("ui.settings.music_volume"))
        self._draw_slider(content_surface, self.music_slider, self.app.audio.music_volume)

        self._draw_row_label(content_surface, self.sfx_volume_row_rect, self.localizer.t("ui.settings.sfx_volume"))
        self._draw_slider(content_surface, self.sfx_slider, self.app.audio.sfx_volume)

        previous_clip = self.app.screen.get_clip()
        self.app.screen.set_clip(self.content_viewport_rect)
        self.app.screen.blit(
            content_surface,
            (self.content_viewport_rect.x, self.content_viewport_rect.y - self.scroll_offset),
        )
        self.app.screen.set_clip(previous_clip)

    def _draw_scrollbar(self):
        if self._max_scroll() <= 0:
            return
        pygame.draw.rect(self.app.screen, (58, 58, 74), self.scrollbar_track_rect, border_radius=6)
        thumb_rect = self._scrollbar_thumb_rect()
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_SELECTED"], thumb_rect, border_radius=6)

    def _mode_title(self, mode):
        titles = {
            "windowed": self.localizer.t("ui.settings.mode_windowed"),
            "fullscreen": self.localizer.t("ui.settings.mode_fullscreen"),
            "borderless": self.localizer.t("ui.settings.mode_borderless"),
        }
        return titles.get(mode, mode)

    def _draw_row_label(self, surface, row_rect, text):
        label = self.section_font.render(text, True, COLORS["UI_TEXT_DIM"])
        label_rect = label.get_rect()
        label_rect.midleft = (row_rect.x + 4, row_rect.centery)
        surface.blit(label, label_rect)

    def _draw_option_button(self, surface, rect, text, active=False, hovered=False):
        fill = (55, 55, 65)
        border = (100, 100, 120)
        if active:
            fill = (64, 90, 120)
            border = COLORS["UI_SLOT_SELECTED"]
        elif hovered:
            fill = (75, 75, 95)
            border = (120, 180, 255)
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=8)
        label = self.button_font.render(text, True, COLORS["WHITE"])
        surface.blit(label, label.get_rect(center=rect.center))

    def _draw_slider(self, surface, slider, value):
        track_rect = slider["track_rect"]
        value_rect = slider["value_rect"]
        pygame.draw.rect(surface, (68, 68, 82), track_rect, border_radius=4)
        fill_width = max(0, min(track_rect.width, int(round(track_rect.width * float(value)))))
        if fill_width > 0:
            fill_rect = pygame.Rect(track_rect.x, track_rect.y, fill_width, track_rect.height)
            pygame.draw.rect(surface, COLORS["UI_SLOT_SELECTED"], fill_rect, border_radius=4)
        handle_x = track_rect.x + int(round(track_rect.width * float(value)))
        handle_x = max(track_rect.x, min(track_rect.right, handle_x))
        pygame.draw.circle(surface, COLORS["WHITE"], (handle_x, track_rect.centery), 9)
        pygame.draw.circle(surface, COLORS["UI_SLOT_SELECTED"], (handle_x, track_rect.centery), 9, width=2)
        percent = self.info_font.render(f"{int(round(float(value) * 100))}%", True, COLORS["WHITE"])
        surface.blit(percent, percent.get_rect(center=value_rect.center))

    def _update_slider_value(self, slider_name, mouse_x):
        slider = self.music_slider if slider_name == "music" else self.sfx_slider
        track_rect = slider["track_rect"]
        normalized = 0.0 if track_rect.width <= 0 else (mouse_x - track_rect.x) / track_rect.width
        normalized = max(0.0, min(1.0, normalized))
        if slider_name == "music":
            self.app.set_music_volume(normalized)
        else:
            self.app.set_sfx_volume(normalized)
