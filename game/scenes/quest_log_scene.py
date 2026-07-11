import pygame

from game.localization import get_localizer
from game.scenes.base import Scene
from settings import COLORS


class QuestLogScene(Scene):
    def __init__(self, app, game_scene):
        self.app = app
        self.game_scene = game_scene
        self.player = game_scene.player
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 47)
        self.section_font = pygame.font.Font(None, 28)
        self.text_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.row_height = 64
        self.entries = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.list_rows = []
        self._selection_initialized = False
        self._layout_size = None
        self._build_layout()

    def _build_layout(self):
        screen_width, screen_height = self.app.get_screen_size()
        self.panel_rect = pygame.Rect(24, 20, screen_width - 48, screen_height - 40)
        self.list_panel = pygame.Rect(self.panel_rect.x + 16, self.panel_rect.y + 76, 300, self.panel_rect.height - 92)
        self.details_panel = pygame.Rect(
            self.list_panel.right + 16,
            self.panel_rect.y + 76,
            self.panel_rect.right - self.list_panel.right - 32,
            self.panel_rect.height - 92,
        )
        self._layout_size = (screen_width, screen_height)

    def _ensure_layout(self):
        if self._layout_size != self.app.get_screen_size():
            self._build_layout()

    def on_language_changed(self):
        self._build_layout()

    def handle_events(self, events):
        self._ensure_layout()
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_j):
                self.app.set_scene(self.game_scene)
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_w):
                self._move_selection(-1)
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_selection(1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
                self._scroll(-self.row_height)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
                self._scroll(self.row_height)

    def update(self, dt):
        return None

    def draw(self):
        self._ensure_layout()
        self.game_scene.draw()

        screen_width, screen_height = self.app.get_screen_size()
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.app.screen.blit(overlay, (0, 0))

        if not self.app.draw_system_background("quests_background", self.panel_rect, border_radius=14, dim_alpha=84):
            pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.panel_rect, border_radius=14)
        else:
            self.app.draw_translucent_panel(self.panel_rect, (24, 26, 34), alpha=72, border_radius=14)

        title = self.title_font.render(self.localizer.t("ui.quests.title"), True, COLORS["WHITE"])
        hint = self.text_font.render(self.localizer.t("ui.quests.close_hint"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(title, title.get_rect(center=(self.panel_rect.centerx, self.panel_rect.y + 30)))
        self.app.screen.blit(hint, (self.panel_rect.right - hint.get_width() - 18, self.panel_rect.y + 24))

        self.app.draw_translucent_panel(self.list_panel, COLORS["UI_PANEL_ALT"], alpha=128, border_radius=12)
        self.app.draw_translucent_panel(self.details_panel, COLORS["UI_PANEL_ALT"], alpha=128, border_radius=12)

        self.entries = self.game_scene.quest_manager.get_quest_log_entries(category="main")
        if self.entries:
            if not self._selection_initialized:
                self._select_initial_entry()
            self.selected_index = max(0, min(self.selected_index, len(self.entries) - 1))
        else:
            self.selected_index = 0
            self._selection_initialized = False

        self._draw_list(self.entries)
        self._draw_details(self.entries)

    def _draw_list(self, entries):
        header = self.section_font.render(self.localizer.t("ui.quests.list_title"), True, COLORS["WHITE"])
        self.app.screen.blit(header, (self.list_panel.x + 12, self.list_panel.y + 12))
        self.list_rows = []

        if not entries:
            text = self.text_font.render(self.localizer.t("ui.quests.empty"), True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(text, (self.list_panel.x + 12, self.list_panel.y + 52))
            return

        visible_area = pygame.Rect(self.list_panel.x + 8, self.list_panel.y + 44, self.list_panel.width - 16, self.list_panel.height - 52)
        content_height = len(entries) * self.row_height
        max_scroll = max(0, content_height - visible_area.height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        previous_clip = self.app.screen.get_clip()
        self.app.screen.set_clip(visible_area)
        draw_y = visible_area.y - self.scroll_offset
        for index, (quest, status) in enumerate(entries):
            row_rect = pygame.Rect(self.list_panel.x + 10, draw_y, self.list_panel.width - 20, 56)
            selected = index == self.selected_index
            fill = COLORS["UI_PANEL"] if selected else COLORS["UI_SLOT"]
            border = self._status_border_color(status, selected)
            pygame.draw.rect(self.app.screen, fill, row_rect, border_radius=10)
            pygame.draw.rect(self.app.screen, border, row_rect, width=2, border_radius=10)

            status_text = self.small_font.render(self.localizer.t(self._status_key(status)), True, self._status_text_color(status))
            title_text = self.text_font.render(self.localizer.t(quest.title_key), True, COLORS["WHITE"])
            self.app.screen.blit(status_text, (row_rect.x + 10, row_rect.y + 8))
            self.app.screen.blit(title_text, (row_rect.x + 10, row_rect.y + 28))
            self.list_rows.append((index, row_rect.copy()))
            draw_y += self.row_height
        self.app.screen.set_clip(previous_clip)

    def _draw_details(self, entries):
        header = self.section_font.render(self.localizer.t("ui.quests.details_title"), True, COLORS["WHITE"])
        self.app.screen.blit(header, (self.details_panel.x + 14, self.details_panel.y + 12))

        if not entries:
            text = self.text_font.render(self.localizer.t("ui.quests.empty"), True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(text, (self.details_panel.x + 14, self.details_panel.y + 52))
            return

        quest, status = entries[self.selected_index]
        draw_y = self.details_panel.y + 52

        title_text = self.section_font.render(self.localizer.t(quest.title_key), True, COLORS["WHITE"])
        status_text = self.small_font.render(self.localizer.t(self._status_key(status)), True, self._status_text_color(status))
        self.app.screen.blit(title_text, (self.details_panel.x + 14, draw_y))
        self.app.screen.blit(status_text, (self.details_panel.right - status_text.get_width() - 14, draw_y + 4))
        draw_y += 30

        for line in self._wrap_text(self.localizer.t(quest.description_key), self.text_font, self.details_panel.width - 28):
            text = self.text_font.render(line, True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(text, (self.details_panel.x + 14, draw_y))
            draw_y += 22

        draw_y += 8
        for objective in quest.objectives:
            objective_status = self.game_scene.quest_manager.build_objective_status(quest, objective, self.localizer)
            prefix = "[x]" if objective_status["completed"] else "[ ]"
            color = (150, 230, 150) if objective_status["completed"] else COLORS["WHITE"]
            for line in self._wrap_text(f"{prefix} {objective_status['text']}", self.text_font, self.details_panel.width - 28):
                text = self.text_font.render(line, True, color)
                self.app.screen.blit(text, (self.details_panel.x + 18, draw_y))
                draw_y += 20

    def _move_selection(self, delta):
        if not self.entries:
            return
        self._selection_initialized = True
        self.selected_index = max(0, min(self.selected_index + delta, len(self.entries) - 1))
        self._ensure_selected_visible()

    def _handle_click(self, mouse_pos):
        for index, rect in self.list_rows:
            if rect.collidepoint(mouse_pos):
                self._selection_initialized = True
                self.selected_index = index
                self._ensure_selected_visible()
                return

    def _scroll(self, delta):
        visible_area_height = self.list_panel.height - 52
        content_height = len(self.entries) * self.row_height
        max_scroll = max(0, content_height - visible_area_height)
        self.scroll_offset = max(0, min(self.scroll_offset + delta, max_scroll))

    def _ensure_selected_visible(self):
        visible_area_height = self.list_panel.height - 52
        top = self.selected_index * self.row_height
        bottom = top + self.row_height
        if top < self.scroll_offset:
            self.scroll_offset = top
        elif bottom > self.scroll_offset + visible_area_height:
            self.scroll_offset = bottom - visible_area_height

    def _select_initial_entry(self):
        self.selected_index = 0
        for index, (_, status) in enumerate(self.entries):
            if status == "active":
                self.selected_index = index
                break
        self._selection_initialized = True
        self._ensure_selected_visible()

    def _status_key(self, status):
        return {
            "active": "ui.quests.status_active",
            "next": "ui.quests.status_next",
            "completed": "ui.quests.status_completed",
        }.get(status, "ui.quests.status_active")

    def _status_text_color(self, status):
        if status == "completed":
            return (150, 230, 150)
        if status == "active":
            return COLORS["UI_SLOT_SELECTED"]
        return COLORS["UI_TEXT_DIM"]

    def _status_border_color(self, status, selected):
        if selected:
            return COLORS["UI_SLOT_SELECTED"]
        if status == "completed":
            return (120, 210, 140)
        if status == "active":
            return COLORS["UI_SLOT_SELECTED"]
        return COLORS["UI_SLOT_BORDER"]

    def _wrap_text(self, text, font, max_width):
        words = str(text).split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for word in words[1:]:
            candidate = current + " " + word
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines
