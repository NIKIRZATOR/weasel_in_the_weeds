import pygame

from game.core.assets import load_image
from game.localization import get_localizer
from game.progression import SKILL_TREE_NODES, get_skill_node_definition
from game.scenes.base import Scene
from settings import COLORS


class ProgressionScene(Scene):
    NODE_RADIUS = 20
    NODE_ICON_SCALE = 1.8

    def __init__(self, app, game_scene):
        self.app = app
        self.game_scene = game_scene
        self.player = game_scene.player
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 52)
        self.section_font = pygame.font.Font(None, 26)
        self.text_font = pygame.font.Font(None, 21)
        self.small_font = pygame.font.Font(None, 17)
        self.message = ""
        self.message_timer = 0.0
        self.selected_node_id = next(iter(SKILL_TREE_NODES))
        self.node_icon_cache = {}
        self.tree_offset_x = 0
        self.tree_offset_y = 0
        self.tree_dragging = False
        self.tree_drag_last_pos = None
        self.unlock_button_rect = None
        self._layout_size = None
        self._build_layout()

    def _build_layout(self):
        screen_width, screen_height = self.app.get_screen_size()
        panel_margin_x = 18
        panel_margin_y = 16
        self.panel_rect = pygame.Rect(panel_margin_x, panel_margin_y, screen_width - panel_margin_x * 2, screen_height - panel_margin_y * 2)
        header_height = 72
        panel_gap = 14
        left_width = min(240, max(210, int(self.panel_rect.width * 0.28)))
        self.left_panel = pygame.Rect(
            self.panel_rect.x + 14,
            self.panel_rect.y + header_height,
            left_width,
            self.panel_rect.height - header_height - 14,
        )
        self.tree_panel = pygame.Rect(
            self.left_panel.right + panel_gap,
            self.panel_rect.y + header_height,
            self.panel_rect.right - (self.left_panel.right + panel_gap) - 14,
            self.panel_rect.height - header_height - 14,
        )
        self._clamp_tree_offset()
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
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_o):
                    self.app.set_scene(self.game_scene)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._try_unlock_selected()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_node_id = self._node_id_at(event.pos)
                if clicked_node_id is not None:
                    if self.selected_node_id == clicked_node_id:
                        self._try_unlock_selected()
                    else:
                        self.selected_node_id = clicked_node_id
                elif self.unlock_button_rect is not None and self.unlock_button_rect.collidepoint(event.pos):
                    self._try_unlock_selected()
                elif self.tree_panel.collidepoint(event.pos):
                    self.tree_dragging = True
                    self.tree_drag_last_pos = event.pos
            elif event.type == pygame.MOUSEMOTION and self.tree_dragging and self.tree_drag_last_pos is not None:
                delta_x = event.pos[0] - self.tree_drag_last_pos[0]
                delta_y = event.pos[1] - self.tree_drag_last_pos[1]
                self.tree_offset_x += delta_x
                self.tree_offset_y += delta_y
                self.tree_drag_last_pos = event.pos
                self._clamp_tree_offset()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.tree_dragging = False
                self.tree_drag_last_pos = None

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0.0:
                self.message = ""

    def draw(self):
        self._ensure_layout()
        self.game_scene.draw()

        screen_width, screen_height = self.app.get_screen_size()
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.app.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.panel_rect, border_radius=14)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.panel_rect, width=2, border_radius=14)

        title = self.title_font.render(self.localizer.t("ui.progression.title"), True, COLORS["WHITE"])
        hint = self.text_font.render(self.localizer.t("ui.progression.close_hint"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(title, (self.panel_rect.x + 20, self.panel_rect.y + 10))
        self.app.screen.blit(hint, (self.panel_rect.right - hint.get_width() - 20, self.panel_rect.y + 20))

        self._draw_info_panel()
        self._draw_tree_panel()

        if self.message:
            message = self.text_font.render(self.message, True, (255, 220, 120))
            self.app.screen.blit(message, message.get_rect(center=(screen_width // 2, screen_height - 22)))

    def _draw_info_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.left_panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.left_panel, width=2, border_radius=12)

        lines = [
            self.localizer.t("ui.progression.level", level=self.player.level),
            self.localizer.t("ui.progression.xp", xp=self.player.xp, required=self.player.get_xp_to_next_level()),
            self.localizer.t("ui.progression.skill_points", points=self.player.skill_points),
        ]
        for index, line in enumerate(lines):
            text = self.section_font.render(line, True, COLORS["WHITE"])
            self.app.screen.blit(text, (self.left_panel.x + 14, self.left_panel.y + 14 + index * 24))

        node = get_skill_node_definition(self.selected_node_id)
        if node is None:
            return

        name = self.section_font.render(node.localized_name(), True, COLORS["WHITE"])
        self.app.screen.blit(name, (self.left_panel.x + 14, self.left_panel.y + 104))

        description = self._wrap_text(node.localized_description(), self.text_font, self.left_panel.width - 32)
        for index, line in enumerate(description):
            text = self.text_font.render(line, True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(text, (self.left_panel.x + 14, self.left_panel.y + 134 + index * 20))

        detail_y = self.left_panel.y + 134 + len(description) * 20 + 18
        for line in self._node_effect_lines(node):
            wrapped_lines = self._wrap_text(line, self.text_font, self.left_panel.width - 32)
            for wrapped_line in wrapped_lines:
                text = self.text_font.render(wrapped_line, True, COLORS["WHITE"])
                self.app.screen.blit(text, (self.left_panel.x + 14, detail_y))
                detail_y += 18
            detail_y += 2

        status = self.localizer.t("ui.progression.unlocked")
        status_color = (120, 220, 160)
        if not self.player.has_unlocked_skill_node(node.id):
            if self.player.can_unlock_skill_node(node.id):
                status = self.localizer.t("ui.progression.unlock_ready")
                status_color = (255, 220, 120)
            else:
                status = self.localizer.t("ui.progression.locked")
                status_color = COLORS["UI_TEXT_DIM"]
        status_lines = self._wrap_text(status, self.section_font, self.left_panel.width - 28)
        status_y = self.left_panel.bottom - 92
        for line in status_lines:
            status_text = self.section_font.render(line, True, status_color)
            self.app.screen.blit(status_text, (self.left_panel.x + 14, status_y))
            status_y += 22

        self.unlock_button_rect = pygame.Rect(self.left_panel.x + 14, self.left_panel.bottom - 52, self.left_panel.width - 28, 34)
        can_unlock = self.player.can_unlock_skill_node(node.id)
        fill = (70, 88, 112) if can_unlock else (52, 52, 60)
        border = COLORS["UI_SLOT_SELECTED"] if can_unlock else COLORS["UI_SLOT_BORDER"]
        pygame.draw.rect(self.app.screen, fill, self.unlock_button_rect, border_radius=8)
        pygame.draw.rect(self.app.screen, border, self.unlock_button_rect, width=2, border_radius=8)
        button_label = self.localizer.t("ui.progression.unlock") if can_unlock else self.localizer.t("ui.progression.requirements")
        button_lines = self._wrap_text(button_label, self.small_font, self.unlock_button_rect.width - 12, max_lines=2)
        self._draw_centered_lines(button_lines, self.small_font, COLORS["WHITE"], self.unlock_button_rect, line_height=14)

    def _draw_tree_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.tree_panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.tree_panel, width=2, border_radius=12)

        clip_previous = self.app.screen.get_clip()
        self.app.screen.set_clip(self.tree_panel.inflate(-4, -4))

        for node in SKILL_TREE_NODES.values():
            start = self._node_center(node.id)
            for required_id in node.requires:
                end = self._node_center(required_id)
                pygame.draw.line(self.app.screen, COLORS["UI_SLOT_BORDER"], start, end, 4)

        for node in SKILL_TREE_NODES.values():
            center = self._node_center(node.id)
            unlocked = self.player.has_unlocked_skill_node(node.id)
            available = self.player.can_unlock_skill_node(node.id)
            selected = node.id == self.selected_node_id
            fill = (66, 70, 82)
            border = COLORS["UI_SLOT_BORDER"]
            if unlocked:
                fill = (88, 140, 106)
                border = (140, 230, 170)
            elif available:
                fill = (96, 96, 70)
                border = (255, 220, 120)
            if selected:
                border = COLORS["UI_SLOT_SELECTED"]

            pygame.draw.circle(self.app.screen, fill, center, self.NODE_RADIUS)
            pygame.draw.circle(self.app.screen, border, center, self.NODE_RADIUS, width=3)

            self._draw_node_icon_or_fallback(node, center)

            label_width = max(64, min(112, self.tree_panel.width // 6))
            label_rect = pygame.Rect(
                center[0] - label_width // 2,
                center[1] + self.NODE_RADIUS + 6,
                label_width,
                34,
            )
            label_lines = self._wrap_text(node.localized_name(), self.small_font, label_rect.width, max_lines=2)
            self._draw_centered_lines(label_lines, self.small_font, COLORS["WHITE"], label_rect, line_height=14)

        self.app.screen.set_clip(clip_previous)

    def _try_unlock_selected(self):
        node = get_skill_node_definition(self.selected_node_id)
        if node is None:
            return
        if self.player.unlock_skill_node(node.id):
            self.message = self.localizer.t("ui.progression.node_unlocked", name=node.localized_name())
            self.message_timer = 1.8
            return
        if self.player.skill_points <= 0:
            self.message = self.localizer.t("ui.progression.no_points")
        else:
            self.message = self.localizer.t("ui.progression.requirements")
        self.message_timer = 1.4

    def _node_id_at(self, mouse_pos):
        for node in SKILL_TREE_NODES.values():
            center = self._node_center(node.id)
            dx = mouse_pos[0] - center[0]
            dy = mouse_pos[1] - center[1]
            if dx * dx + dy * dy <= self.NODE_RADIUS * self.NODE_RADIUS:
                return node.id
        return None

    def _node_center(self, node_id):
        node = get_skill_node_definition(node_id)
        if node is None:
            return (0, 0)
        return (
            self.tree_panel.x + node.position[0] + self.tree_offset_x,
            self.tree_panel.y + node.position[1] + self.tree_offset_y,
        )

    def _draw_node_icon_or_fallback(self, node, center):
        icon = self._get_node_icon(node)
        if icon is not None:
            self.app.screen.blit(icon, icon.get_rect(center=center))
            return
        short_label = self.small_font.render(node.localized_name()[:1].upper(), True, COLORS["WHITE"])
        self.app.screen.blit(short_label, short_label.get_rect(center=center))

    def _get_node_icon(self, node):
        if node.icon_path is None:
            return None
        cache_key = (node.id, self.NODE_RADIUS, self.NODE_ICON_SCALE)
        if cache_key in self.node_icon_cache:
            return self.node_icon_cache[cache_key]
        size = int(self.NODE_RADIUS * self.NODE_ICON_SCALE)
        icon = load_image(node.icon_path, (size, size))
        self.node_icon_cache[cache_key] = icon
        return icon

    def _clamp_tree_offset(self):
        if self.tree_panel.width <= 0 or self.tree_panel.height <= 0:
            self.tree_offset_x = 0
            self.tree_offset_y = 0
            return

        node_positions = [node.position for node in SKILL_TREE_NODES.values()]
        if not node_positions:
            self.tree_offset_x = 0
            self.tree_offset_y = 0
            return

        min_x = min(position[0] for position in node_positions) - self.NODE_RADIUS - 40
        max_x = max(position[0] for position in node_positions) + self.NODE_RADIUS + 120
        min_y = min(position[1] for position in node_positions) - self.NODE_RADIUS - 40
        max_y = max(position[1] for position in node_positions) + self.NODE_RADIUS + 60
        content_width = max_x - min_x
        content_height = max_y - min_y

        if content_width <= self.tree_panel.width:
            self.tree_offset_x = (self.tree_panel.width - content_width) // 2 - min_x
        else:
            min_offset_x = self.tree_panel.width - max_x
            max_offset_x = -min_x
            self.tree_offset_x = max(min_offset_x, min(max_offset_x, self.tree_offset_x))

        if content_height <= self.tree_panel.height:
            self.tree_offset_y = (self.tree_panel.height - content_height) // 2 - min_y
        else:
            min_offset_y = self.tree_panel.height - max_y
            max_offset_y = -min_y
            self.tree_offset_y = max(min_offset_y, min(max_offset_y, self.tree_offset_y))

    def _node_effect_lines(self, node):
        bonuses = node.bonuses
        lines = []
        if bonuses.stats.max_health:
            lines.append(self.localizer.t("ui.progression.effect_health", value=bonuses.stats.max_health))
        if bonuses.stats.max_stamina:
            lines.append(self.localizer.t("ui.progression.effect_stamina", value=bonuses.stats.max_stamina))
        if bonuses.stats.attack:
            lines.append(self.localizer.t("ui.progression.effect_attack", value=bonuses.stats.attack))
        if bonuses.stats.defense:
            lines.append(self.localizer.t("ui.progression.effect_defense", value=bonuses.stats.defense))
        if bonuses.stats.speed:
            lines.append(self.localizer.t("ui.progression.effect_speed", value=bonuses.stats.speed))
        if bonuses.attack_move_speed_multiplier_bonus:
            lines.append(
                self.localizer.t(
                    "ui.progression.effect_attack_move",
                    value=int(bonuses.attack_move_speed_multiplier_bonus * 100),
                )
            )
        if bonuses.light_stamina_cost_multiplier < 1.0:
            lines.append(
                self.localizer.t(
                    "ui.progression.effect_light_cost",
                    value=int((1.0 - bonuses.light_stamina_cost_multiplier) * 100),
                )
            )
        if bonuses.heavy_stamina_cost_multiplier < 1.0:
            lines.append(
                self.localizer.t(
                    "ui.progression.effect_heavy_cost",
                    value=int((1.0 - bonuses.heavy_stamina_cost_multiplier) * 100),
                )
            )
        if bonuses.charged_stamina_cost_multiplier < 1.0:
            lines.append(
                self.localizer.t(
                    "ui.progression.effect_charged_cost",
                    value=int((1.0 - bonuses.charged_stamina_cost_multiplier) * 100),
                )
            )
        if bonuses.bow_damage_bonus:
            lines.append(self.localizer.t("ui.progression.effect_bow_damage", value=bonuses.bow_damage_bonus))
        if bonuses.charged_damage_bonus:
            lines.append(self.localizer.t("ui.progression.effect_charged_damage", value=bonuses.charged_damage_bonus))
        if bonuses.recovery_multiplier < 1.0:
            lines.append(
                self.localizer.t(
                    "ui.progression.effect_recovery",
                    value=int((1.0 - bonuses.recovery_multiplier) * 100),
                )
            )
        if bonuses.charge_time_multiplier < 1.0:
            lines.append(
                self.localizer.t(
                    "ui.progression.effect_charge_time",
                    value=int((1.0 - bonuses.charge_time_multiplier) * 100),
                )
            )
        if node.requires:
            lines.append(
                self.localizer.t(
                    "ui.progression.requires",
                    names=", ".join(get_skill_node_definition(required_id).localized_name() for required_id in node.requires),
                )
            )
        return lines

    def _wrap_text(self, text, font, max_width, max_lines=None):
        words = text.split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue
            if max_lines is not None and len(lines) >= max_lines - 1:
                break
            lines.append(current)
            current = word
        lines.append(current)
        if max_lines is not None and len(lines) > max_lines:
            lines = lines[:max_lines]
        return lines

    def _draw_centered_lines(self, lines, font, color, rect, line_height):
        total_height = len(lines) * line_height
        start_y = rect.y + max(0, (rect.height - total_height) // 2)
        for index, line in enumerate(lines):
            text = font.render(line, True, color)
            text_rect = text.get_rect(center=(rect.centerx, start_y + index * line_height + line_height // 2))
            self.app.screen.blit(text, text_rect)
