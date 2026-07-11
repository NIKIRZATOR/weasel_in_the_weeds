from pathlib import Path

import pygame

from game.localization import get_localizer
from game.scenes.base import Scene
from game.scenes.menu_background import AnimatedMenuBackground
from settings import COLORS


class SaveSlotsScene(Scene):
    ROW_HEIGHT = 72
    ROW_GAP = 8
    BUTTON_WIDTH = 236
    BUTTON_HEIGHT = 44
    BUTTON_GAP = 24
    CREATE_BUTTON_WIDTH = 300

    def __init__(self, app, previous_scene, mode="continue"):
        self.app = app
        self.app.audio.play_music("system_main_menu")
        self.previous_scene = previous_scene
        self.mode = str(mode)
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 60)
        self.text_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        self.message = ""
        self.message_timer = 0.0
        self.input_text = ""
        self.selected_index = 0
        self.scroll_offset = 0
        self.slot_rects: list[tuple[pygame.Rect, int]] = []
        self.confirm_delete = False
        self.scroll_track_rect = None
        self.scroll_thumb_rect = None
        self.scroll_drag_active = False
        self.scroll_drag_offset_y = 0
        self._layout_size = None
        self.background = AnimatedMenuBackground(pan_seconds=20.0, blur_divisor=8, overlay_color=(10, 12, 18, 124))
        self._refresh_slots()

    def _refresh_slots(self):
        self.slots = self.app.save_manager.list_slots()
        if self.slots:
            self.selected_index = max(0, min(self.selected_index, len(self.slots) - 1))
        else:
            self.selected_index = 0
            self.scroll_offset = 0
            self.confirm_delete = False
        self._ensure_selection_visible()
        self._layout_size = None

    def _ensure_layout(self):
        if self._layout_size == self.app.get_screen_size():
            return
        self._layout_size = self.app.get_screen_size()
        self.background.recalculate()
        screen_width, screen_height = self._layout_size
        self.input_rect = pygame.Rect((screen_width - 420) // 2, 120, 420, 42)
        self.create_rect = pygame.Rect((screen_width - self.CREATE_BUTTON_WIDTH) // 2, 176, self.CREATE_BUTTON_WIDTH, 42)
        list_top = 220 if self.mode == "continue" else 238
        reserved_footer_height = 20
        reserved_actions_height = 108 if self.mode == "continue" else 0
        list_height = max(260, min(420, screen_height - list_top - reserved_actions_height - reserved_footer_height))
        self.list_rect = pygame.Rect((screen_width - 620) // 2, list_top, 620, list_height)

        total_buttons_width = self.BUTTON_WIDTH * 2 + self.BUTTON_GAP
        buttons_start_x = (screen_width - total_buttons_width) // 2
        button_y = self.list_rect.bottom + 22
        self.continue_rect = pygame.Rect(buttons_start_x, button_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.delete_rect = pygame.Rect(
            buttons_start_x + self.BUTTON_WIDTH + self.BUTTON_GAP,
            button_y,
            self.BUTTON_WIDTH,
            self.BUTTON_HEIGHT,
        )
        self.cancel_delete_rect = pygame.Rect(buttons_start_x, button_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.confirm_delete_rect = pygame.Rect(
            buttons_start_x + self.BUTTON_WIDTH + self.BUTTON_GAP,
            button_y,
            self.BUTTON_WIDTH,
            self.BUTTON_HEIGHT,
        )

    def on_language_changed(self):
        self._refresh_slots()

    def set_message(self, text):
        self.message = text
        self.message_timer = 2.0

    def _title_key(self):
        return "ui.saves.title_new" if self.mode == "new" else "ui.saves.title_continue"

    def _visible_row_capacity(self):
        usable_height = max(0, self.list_rect.height - 16)
        step = self.ROW_HEIGHT + self.ROW_GAP
        return max(1, usable_height // step)

    def _ensure_selection_visible(self):
        visible_count = max(1, getattr(self, "_visible_count_cache", 4))
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        max_top = max(0, self.selected_index - visible_count + 1)
        if self.selected_index >= self.scroll_offset + visible_count:
            self.scroll_offset = max_top

        max_scroll = max(0, len(self.slots) - visible_count)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def _selected_slot(self):
        if not self.slots:
            return None
        return self.slots[self.selected_index]

    def _activate_selected_slot(self):
        slot = self._selected_slot()
        if slot is None:
            self.set_message(self.localizer.t("ui.saves.no_slots"))
            return False
        started = self.app.continue_game(slot.slot_id)
        if not started:
            self.set_message(self.localizer.t("ui.saves.load_failed"))
            self._refresh_slots()
        return started

    def _delete_selected_slot(self):
        slot = self._selected_slot()
        if slot is None:
            self.set_message(self.localizer.t("ui.saves.no_slots"))
            return False
        deleted = self.app.save_manager.delete_slot(slot.slot_id)
        if not deleted:
            self.set_message(self.localizer.t("ui.saves.delete_failed"))
            return False
        self.set_message(self.localizer.t("ui.saves.delete_success", title=slot.title))
        self.confirm_delete = False
        self._refresh_slots()
        return True

    def _create_slot(self):
        slot = self.app.save_manager.create_slot(self.input_text)
        self.input_text = ""
        self.confirm_delete = False
        self._refresh_slots()
        if not self.app.start_new_game(slot.slot_id):
            self.set_message(self.localizer.t("ui.saves.create_failed"))
            return False
        return True

    def _handle_text_input(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
            return
        if event.key == pygame.K_RETURN:
            self._create_slot()
            return
        if event.unicode and event.unicode.isprintable() and len(self.input_text) < 24:
            self.input_text += event.unicode

    def _move_selection(self, direction):
        if not self.slots:
            return
        self.selected_index = (self.selected_index + direction) % len(self.slots)
        self.confirm_delete = False
        self._ensure_selection_visible()

    def _scroll_selection(self, direction):
        if not self.slots:
            return
        self.selected_index = max(0, min(len(self.slots) - 1, self.selected_index + direction))
        self.confirm_delete = False
        self._ensure_selection_visible()

    def _scroll_list(self, direction):
        if not self.slots:
            return
        visible_count = max(1, self._visible_row_capacity())
        max_scroll = max(0, len(self.slots) - visible_count)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset + direction))
        if self.selected_index < self.scroll_offset:
            self.selected_index = self.scroll_offset
        elif self.selected_index >= self.scroll_offset + visible_count:
            self.selected_index = self.scroll_offset + visible_count - 1
        self.confirm_delete = False

    def _scrollbar_metrics(self):
        visible_count = max(1, self._visible_row_capacity())
        if len(self.slots) <= visible_count:
            return None, None

        track_rect = pygame.Rect(
            self.list_rect.right - 14,
            self.list_rect.y + 12,
            6,
            self.list_rect.height - 24,
        )
        thumb_height = max(28, int(track_rect.height * (visible_count / len(self.slots))))
        max_scroll = max(1, len(self.slots) - visible_count)
        thumb_y = track_rect.y + int((track_rect.height - thumb_height) * (self.scroll_offset / max_scroll))
        thumb_rect = pygame.Rect(track_rect.x, thumb_y, track_rect.width, thumb_height)
        return track_rect, thumb_rect

    def _update_scroll_from_thumb_top(self, thumb_top):
        metrics = self._scrollbar_metrics()
        if metrics == (None, None):
            return
        track_rect, thumb_rect = metrics
        visible_count = max(1, self._visible_row_capacity())
        max_scroll = max(0, len(self.slots) - visible_count)
        max_thumb_top = max(track_rect.y, track_rect.bottom - thumb_rect.height)
        clamped_top = max(track_rect.y, min(max_thumb_top, int(thumb_top)))

        if max_scroll <= 0 or max_thumb_top == track_rect.y:
            self.scroll_offset = 0
        else:
            progress = (clamped_top - track_rect.y) / max(1, (max_thumb_top - track_rect.y))
            self.scroll_offset = int(round(progress * max_scroll))

        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset))
        if self.selected_index < self.scroll_offset:
            self.selected_index = self.scroll_offset
        elif self.selected_index >= self.scroll_offset + visible_count:
            self.selected_index = self.scroll_offset + visible_count - 1
        self.confirm_delete = False

    def _slot_subtitle(self, slot):
        if slot.current_level:
            level_key = f"ui.levels.{Path(slot.current_level).stem}"
            translated_level = self.localizer.t(level_key)
            level_name = translated_level if translated_level != level_key else slot.current_level
        else:
            level_name = self.localizer.t("ui.saves.level_unknown")
        checkpoint_name = slot.last_checkpoint_name or self.localizer.t("ui.saves.no_checkpoint")
        return self.localizer.t(
            "ui.saves.slot_summary",
            level=level_name,
            player_level=slot.player_level,
            checkpoint=checkpoint_name,
        )

    def _handle_slot_click(self, mouse_pos):
        for index, (rect, absolute_index) in enumerate(self.slot_rects):
            if not rect.collidepoint(mouse_pos):
                continue
            self.selected_index = absolute_index
            self.confirm_delete = False
            self._ensure_selection_visible()
            return True
        return False

    def handle_events(self, events):
        self._ensure_layout()
        self._visible_count_cache = self._visible_row_capacity()
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.scroll_drag_active = False
            elif event.type == pygame.MOUSEMOTION and self.scroll_drag_active:
                if self.scroll_thumb_rect is not None:
                    self._update_scroll_from_thumb_top(event.pos[1] - self.scroll_drag_offset_y)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.confirm_delete:
                    self.confirm_delete = False
                else:
                    self.app.set_scene(self.previous_scene)
            elif event.type == pygame.KEYDOWN and self.mode == "new":
                self._handle_text_input(event)
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_w):
                self._move_selection(-1)
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_selection(1)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
                self._scroll_selection(-self._visible_count_cache)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
                self._scroll_selection(self._visible_count_cache)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if self.mode == "new":
                    self._create_slot()
                elif self.confirm_delete:
                    self._delete_selected_slot()
                else:
                    self._activate_selected_slot()
            elif event.type == pygame.MOUSEWHEEL:
                if self.list_rect.collidepoint(mouse_pos):
                    self._scroll_list(-event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.scroll_thumb_rect is not None and self.scroll_thumb_rect.collidepoint(mouse_pos):
                    self.scroll_drag_active = True
                    self.scroll_drag_offset_y = mouse_pos[1] - self.scroll_thumb_rect.y
                    return
                if self.scroll_track_rect is not None and self.scroll_track_rect.collidepoint(mouse_pos):
                    if self.scroll_thumb_rect is not None:
                        self._update_scroll_from_thumb_top(mouse_pos[1] - self.scroll_thumb_rect.height // 2)
                    return
                if self.mode == "new" and self.create_rect.collidepoint(mouse_pos):
                    self._create_slot()
                    return
                if self._handle_slot_click(mouse_pos):
                    return
                if self.mode != "continue":
                    continue
                if self.confirm_delete:
                    if self.cancel_delete_rect.collidepoint(mouse_pos):
                        self.confirm_delete = False
                        return
                    if self.confirm_delete_rect.collidepoint(mouse_pos):
                        self._delete_selected_slot()
                        return
                else:
                    if self.continue_rect.collidepoint(mouse_pos):
                        self._activate_selected_slot()
                        return
                    if self.delete_rect.collidepoint(mouse_pos):
                        if self._selected_slot() is not None:
                            self.confirm_delete = True
                        return

    def update(self, dt):
        self.background.update(dt)
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0.0:
                self.message = ""

    def _draw_action_button(self, rect, label, *, hovered=False, danger=False, disabled=False):
        fill = COLORS["UI_PANEL_ALT"] if not danger else (96, 54, 54)
        border = COLORS["UI_SLOT_SELECTED"] if not danger else (220, 120, 120)
        text_color = COLORS["WHITE"] if not disabled else COLORS["UI_TEXT_DIM"]
        if hovered and not disabled:
            fill = COLORS["UI_SLOT"] if not danger else (120, 66, 66)
        if disabled:
            fill = (48, 48, 56)
            border = COLORS["UI_SLOT_BORDER"]

        pygame.draw.rect(self.app.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)
        label_surface = self.text_font.render(label, True, text_color)
        self.app.screen.blit(label_surface, label_surface.get_rect(center=rect.center))

    def draw(self):
        self._ensure_layout()
        self._visible_count_cache = self._visible_row_capacity()
        self._ensure_selection_visible()
        screen_width, screen_height = self.app.get_screen_size()
        self.background.draw(self.app.screen)
        self.slot_rects = []
        self.scroll_track_rect = None
        self.scroll_thumb_rect = None

        title = self.title_font.render(self.localizer.t(self._title_key()), True, COLORS["WHITE"])
        self.app.screen.blit(title, title.get_rect(center=(screen_width // 2, 58)))

        if self.mode == "new":
            hint = self.small_font.render(self.localizer.t("ui.saves.new_hint"), True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(hint, hint.get_rect(center=(screen_width // 2, 98)))

            pygame.draw.rect(self.app.screen, COLORS["UI_SLOT"], self.input_rect, border_radius=8)
            pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.input_rect, width=2, border_radius=8)
            input_value = self.input_text or self.localizer.t("ui.saves.default_name")
            input_color = COLORS["WHITE"] if self.input_text else COLORS["UI_TEXT_DIM"]
            input_surface = self.text_font.render(input_value, True, input_color)
            self.app.screen.blit(
                input_surface,
                input_surface.get_rect(midleft=(self.input_rect.x + 12, self.input_rect.centery)),
            )

            pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.create_rect, border_radius=8)
            pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_SELECTED"], self.create_rect, width=2, border_radius=8)
            create_label = self.text_font.render(self.localizer.t("ui.saves.create_button"), True, COLORS["WHITE"])
            self.app.screen.blit(create_label, create_label.get_rect(center=self.create_rect.center))
        else:
            hint = self.small_font.render(self.localizer.t("ui.saves.continue_hint"), True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(hint, hint.get_rect(center=(screen_width // 2, 108)))

        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.list_rect, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.list_rect, width=2, border_radius=12)

        if not self.slots:
            empty_label = self.text_font.render(self.localizer.t("ui.saves.no_slots"), True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(empty_label, empty_label.get_rect(center=self.list_rect.center))
        else:
            visible_top = self.list_rect.y + 8
            visible_left = self.list_rect.x + 12
            visible_width = self.list_rect.width - 34
            visible_slots = self.slots[self.scroll_offset:self.scroll_offset + self._visible_count_cache]
            for relative_index, slot in enumerate(visible_slots):
                absolute_index = self.scroll_offset + relative_index
                rect = pygame.Rect(
                    visible_left,
                    visible_top + relative_index * (self.ROW_HEIGHT + self.ROW_GAP),
                    visible_width,
                    self.ROW_HEIGHT,
                )
                selected = absolute_index == self.selected_index
                fill = COLORS["UI_PANEL_ALT"] if selected else COLORS["UI_SLOT"]
                border = COLORS["UI_SLOT_SELECTED"] if selected else COLORS["UI_SLOT_BORDER"]
                pygame.draw.rect(self.app.screen, fill, rect, border_radius=10)
                pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=10)

                title_surface = self.text_font.render(slot.title, True, COLORS["WHITE"])
                subtitle_surface = self.small_font.render(self._slot_subtitle(slot), True, COLORS["UI_TEXT_DIM"])
                self.app.screen.blit(title_surface, title_surface.get_rect(topleft=(rect.x + 14, rect.y + 10)))
                self.app.screen.blit(subtitle_surface, subtitle_surface.get_rect(topleft=(rect.x + 14, rect.y + 39)))
                self.slot_rects.append((rect, absolute_index))

            if len(self.slots) > self._visible_count_cache:
                track_rect, thumb_rect = self._scrollbar_metrics()
                self.scroll_track_rect = track_rect
                self.scroll_thumb_rect = thumb_rect
                pygame.draw.rect(self.app.screen, COLORS["UI_SLOT"], track_rect, border_radius=4)
                pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_SELECTED"], thumb_rect, border_radius=4)

        if self.mode == "continue":
            mouse_pos = pygame.mouse.get_pos()
            selected_slot = self._selected_slot()
            if self.confirm_delete:
                confirm_text = self.localizer.t(
                    "ui.saves.delete_confirm",
                    title=selected_slot.title if selected_slot is not None else "",
                )
                confirm_surface = self.small_font.render(confirm_text, True, COLORS["WHITE"])
                self.app.screen.blit(
                    confirm_surface,
                    confirm_surface.get_rect(center=(screen_width // 2, self.continue_rect.y - 16)),
                )
                self._draw_action_button(
                    self.cancel_delete_rect,
                    self.localizer.t("ui.saves.cancel_button"),
                    hovered=self.cancel_delete_rect.collidepoint(mouse_pos),
                )
                self._draw_action_button(
                    self.confirm_delete_rect,
                    self.localizer.t("ui.saves.confirm_delete_button"),
                    hovered=self.confirm_delete_rect.collidepoint(mouse_pos),
                    danger=True,
                    disabled=selected_slot is None,
                )
            else:
                self._draw_action_button(
                    self.continue_rect,
                    self.localizer.t("ui.saves.continue_button"),
                    hovered=self.continue_rect.collidepoint(mouse_pos),
                    disabled=selected_slot is None,
                )
                self._draw_action_button(
                    self.delete_rect,
                    self.localizer.t("ui.saves.delete_button"),
                    hovered=self.delete_rect.collidepoint(mouse_pos),
                    danger=True,
                    disabled=selected_slot is None,
                )

        if self.message:
            message_surface = self.small_font.render(self.message, True, (255, 220, 120))
            message_y = screen_height - 24
            if self.mode == "continue":
                message_y = max(message_y, self.continue_rect.bottom + 24)
            self.app.screen.blit(message_surface, message_surface.get_rect(center=(screen_width // 2, message_y)))
