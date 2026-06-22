from __future__ import annotations

from math import ceil

import pygame

from game.items import get_item_icon
from game.items.types import ItemKind
from game.localization import get_localizer
from game.scenes.base import Scene
from settings import COLORS, INVENTORY_COLUMNS


class ContainerInventoryScene(Scene):
    """Side-by-side player and world-container inventories."""

    def __init__(self, app, game_scene, container):
        self.app = app
        self.game_scene = game_scene
        self.player = game_scene.player
        self.container = container
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 48)
        self.section_font = pygame.font.Font(None, 30)
        self.text_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.selected_slot = None
        self.pressed_slot = None
        self.drag_source = None
        self.drag_start_pos = None
        self.dragging = False
        self.drag_threshold = 6
        self._layout_size = None
        self._build_layout()

    def _build_layout(self):
        screen_width, screen_height = self.app.get_screen_size()
        player_capacity = self.player.inventory.capacity
        layout_size = (screen_width, screen_height, player_capacity)
        if self._layout_size == layout_size:
            return
        self._layout_size = layout_size

        self.slot_size = 52 if screen_width >= 760 else 44
        self.slot_gap = 9
        self.player_columns = INVENTORY_COLUMNS
        self.container_columns = 5
        self.player_rows = max(1, ceil(player_capacity / self.player_columns))
        self.container_rows = max(1, ceil(self.container.inventory.capacity / self.container_columns))

        panel_width = min(screen_width - 32, 760)
        grid_width = 5 * self.slot_size + 4 * self.slot_gap
        column_width = grid_width + 32
        gap = 20
        body_height = max(self.player_rows, self.container_rows) * (self.slot_size + self.slot_gap) + 82
        panel_height = min(screen_height - 28, max(350, body_height + 150))
        self.panel_rect = pygame.Rect(
            (screen_width - panel_width) // 2,
            (screen_height - panel_height) // 2,
            panel_width,
            panel_height,
        )
        columns_width = column_width * 2 + gap
        columns_x = self.panel_rect.centerx - columns_width // 2
        columns_y = self.panel_rect.y + 72
        self.player_panel = pygame.Rect(columns_x, columns_y, column_width, body_height)
        self.container_panel = pygame.Rect(columns_x + column_width + gap, columns_y, column_width, body_height)
        self.player_origin = (self.player_panel.x + 16, self.player_panel.y + 52)
        self.container_origin = (self.container_panel.x + 16, self.container_panel.y + 52)
        self.details_panel = pygame.Rect(
            self.panel_rect.x + 22,
            self.panel_rect.bottom - 68,
            self.panel_rect.width - 44,
            48,
        )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_e):
                self.close()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_button_down(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_motion(event.pos, event.buttons)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._handle_button_up(event.pos)

    def close(self):
        self.container.close()
        self.app.set_scene(self.game_scene)

    def _handle_button_down(self, mouse_pos):
        self._build_layout()
        slot = self._slot_at(mouse_pos)
        self.pressed_slot = slot
        self.drag_source = None
        self.drag_start_pos = None
        self.dragging = False
        if slot is not None and self._get_stack(*slot) is not None:
            self.drag_start_pos = mouse_pos

    def _handle_motion(self, mouse_pos, buttons):
        if self.pressed_slot is None or self.drag_start_pos is None or not buttons[0] or self.dragging:
            return
        dx = mouse_pos[0] - self.drag_start_pos[0]
        dy = mouse_pos[1] - self.drag_start_pos[1]
        if dx * dx + dy * dy >= self.drag_threshold * self.drag_threshold:
            self.drag_source = self.pressed_slot
            self.dragging = True

    def _handle_button_up(self, mouse_pos):
        target = self._slot_at(mouse_pos)
        if self.dragging and self.drag_source is not None:
            if target is not None and target != self.drag_source:
                if self._transfer(self.drag_source, target):
                    self.selected_slot = target
                else:
                    self.selected_slot = self.drag_source
            else:
                self.selected_slot = self.drag_source
        elif self.pressed_slot is not None and target == self.pressed_slot:
            self.selected_slot = None if self.selected_slot == target else target
        else:
            self.selected_slot = None

        self.pressed_slot = None
        self.drag_source = None
        self.drag_start_pos = None
        self.dragging = False

    def _transfer(self, source, target):
        source_kind, source_index = source
        target_kind, target_index = target
        source_stack = self._get_stack(source_kind, source_index)
        target_stack = self._get_stack(target_kind, target_index)
        if source_stack is None:
            return False

        if (
            source_kind == "container"
            and target_kind == "player"
            and source_stack.kind == ItemKind.CURRENCY
        ):
            if not self.player.pickup_item(item_stack=source_stack):
                return False
            self._set_stack(source_kind, source_index, None)
            self.container.save_state()
            return True

        if target_stack is None:
            self._set_stack(target_kind, target_index, source_stack)
            self._set_stack(source_kind, source_index, None)
        elif source_stack.can_stack_with(target_stack):
            transferred = min(source_stack.quantity, target_stack.available_space())
            if transferred <= 0:
                return False
            target_stack.quantity += transferred
            source_stack.quantity -= transferred
            if source_stack.quantity <= 0:
                self._set_stack(source_kind, source_index, None)
        else:
            self._set_stack(source_kind, source_index, target_stack)
            self._set_stack(target_kind, target_index, source_stack)

        self.player._sync_inventory_capacities()
        self.container.save_state()
        return True

    def _inventory_for(self, kind):
        return self.player.inventory if kind == "player" else self.container.inventory

    def _get_stack(self, kind, index):
        return self._inventory_for(kind).get_stack_at(index)

    def _set_stack(self, kind, index, stack):
        return self._inventory_for(kind).set_stack_at(index, stack)

    def update(self, dt):
        return None

    def draw(self):
        self._build_layout()
        self.game_scene.draw()
        screen_width, screen_height = self.app.get_screen_size()
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.app.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.panel_rect, border_radius=14)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.panel_rect, width=2, border_radius=14)
        title = self.title_font.render(self.localizer.t("ui.container.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, (self.panel_rect.x + 24, self.panel_rect.y + 14))
        hint = self.small_font.render(self.localizer.t("ui.container.close_hint"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(hint, (self.panel_rect.right - hint.get_width() - 24, self.panel_rect.y + 24))

        self._draw_inventory_panel(
            "player",
            self.player_panel,
            self.player_origin,
            self.player.inventory.capacity,
            self.player_columns,
            self.localizer.t("ui.container.player_inventory"),
        )
        self._draw_inventory_panel(
            "container",
            self.container_panel,
            self.container_origin,
            self.container.inventory.capacity,
            self.container_columns,
            self.container.name,
        )
        self._draw_details()
        self._draw_drag_preview()

    def _draw_inventory_panel(self, kind, panel, origin, capacity, columns, title):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], panel, width=2, border_radius=12)
        label = self.section_font.render(title, True, COLORS["WHITE"])
        self.app.screen.blit(label, (panel.x + 14, panel.y + 14))
        for index in range(capacity):
            rect = self._slot_rect(origin, index, columns)
            selected = self.selected_slot == (kind, index)
            stack = self._get_stack(kind, index)
            if self.dragging and self.drag_source == (kind, index):
                stack = None
            pygame.draw.rect(self.app.screen, COLORS["UI_SLOT"], rect, border_radius=8)
            border = COLORS["UI_SLOT_SELECTED"] if selected else COLORS["UI_SLOT_BORDER"]
            pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)
            if stack is not None:
                self._draw_stack(stack, rect)

    def _draw_stack(self, stack, rect):
        icon = get_item_icon(stack.definition, (rect.width - 12, rect.height - 12))
        if icon is not None:
            self.app.screen.blit(icon, icon.get_rect(center=rect.center))
        else:
            label = self.text_font.render(stack.name[:2].upper(), True, COLORS["WHITE"])
            self.app.screen.blit(label, label.get_rect(center=rect.center))
        if stack.quantity > 1:
            quantity = self.small_font.render(str(stack.quantity), True, COLORS["WHITE"])
            self.app.screen.blit(quantity, (rect.right - quantity.get_width() - 4, rect.bottom - quantity.get_height() - 2))

    def _draw_details(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.details_panel, border_radius=8)
        stack = self._get_stack(*self.selected_slot) if self.selected_slot is not None else None
        if stack is None:
            text = self.small_font.render(self.localizer.t("ui.container.drag_hint"), True, COLORS["UI_TEXT_DIM"])
        else:
            text = self.small_font.render(f"{stack.name}: {stack.description}", True, COLORS["WHITE"])
        self.app.screen.blit(text, (self.details_panel.x + 12, self.details_panel.y + 14))

    def _draw_drag_preview(self):
        if not self.dragging or self.drag_source is None:
            return
        stack = self._get_stack(*self.drag_source)
        if stack is None:
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        rect = pygame.Rect(mouse_x - self.slot_size // 2, mouse_y - self.slot_size // 2, self.slot_size, self.slot_size)
        preview = pygame.Surface(rect.size, pygame.SRCALPHA)
        preview.fill((60, 60, 76, 225))
        icon = get_item_icon(stack.definition, (rect.width - 12, rect.height - 12))
        if icon is not None:
            preview.blit(icon, icon.get_rect(center=preview.get_rect().center))
        else:
            label = self.text_font.render(stack.name[:2].upper(), True, COLORS["WHITE"])
            preview.blit(label, label.get_rect(center=preview.get_rect().center))
        self.app.screen.blit(preview, rect)

    def _slot_at(self, mouse_pos):
        for kind, origin, inventory, columns in (
            ("player", self.player_origin, self.player.inventory, self.player_columns),
            ("container", self.container_origin, self.container.inventory, self.container_columns),
        ):
            for index in range(inventory.capacity):
                if self._slot_rect(origin, index, columns).collidepoint(mouse_pos):
                    return kind, index
        return None

    def _slot_rect(self, origin, index, columns):
        row, col = divmod(index, columns)
        x = origin[0] + col * (self.slot_size + self.slot_gap)
        y = origin[1] + row * (self.slot_size + self.slot_gap)
        return pygame.Rect(x, y, self.slot_size, self.slot_size)
