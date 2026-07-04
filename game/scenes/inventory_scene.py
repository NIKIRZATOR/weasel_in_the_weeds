import pygame
from math import ceil

from game.items import get_item_definition, get_item_icon
from game.items.types import EquipSlot, ItemKind
from game.localization import get_localizer
from game.scenes.base import Scene
from settings import COLORS, HOTBAR_SIZE, INVENTORY_COLUMNS, SCREEN_HEIGHT, SCREEN_WIDTH


class InventoryScene(Scene):
    QUEST_COLUMNS = 2
    QUEST_ROWS = 5

    def __init__(self, app, game_scene):
        self.app = app
        self.game_scene = game_scene
        self.player = game_scene.player
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 62)
        self.section_font = pygame.font.Font(None, 30)
        self.panel_title_font = pygame.font.Font(None, 24)
        self.text_font = pygame.font.Font(None, 24)
        self.stats_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 20)
        self.message = ""
        self.message_timer = 0.0
        self.selected_slot = None
        self.pressed_slot = None
        self.drag_source = None
        self.drag_start_pos = None
        self.dragging = False
        self.drag_threshold = 6
        self.header_currency_targets = []
        self._layout_size = None
        self._build_layout()

    def _build_layout(self):
        screen_width, screen_height = self.app.get_screen_size()
        layout_size = (screen_width, screen_height)
        if self._layout_size == layout_size:
            return
        self._layout_size = layout_size

        panel_width = min(SCREEN_WIDTH - 60, screen_width - 40)
        panel_height = min(SCREEN_HEIGHT - 48, screen_height - 32)
        compact = panel_width < 1120 or panel_height < 700
        outer_margin_x = max(20, (screen_width - panel_width) // 2)
        outer_margin_y = max(16, (screen_height - panel_height) // 2)
        self.panel_rect = pygame.Rect(outer_margin_x, outer_margin_y, panel_width, panel_height)

        self.panel_padding = 20 if compact else 24
        self.column_gap = 10 if compact else 16
        self.inventory_slot_size = 40 if compact else 48
        self.inventory_gap = 8
        self.inventory_columns = INVENTORY_COLUMNS
        self.inventory_slot_count = self.player.inventory.capacity
        self.inventory_rows = max(1, ceil(self.inventory_slot_count / self.inventory_columns))
        self.quest_slot_count = self.player.quest_inventory.capacity

        left_width = 178 if compact else 200
        side_width = 106 if compact else 124
        center_width = self.inventory_columns * self.inventory_slot_size
        center_width += (self.inventory_columns - 1) * self.inventory_gap + 32

        content_top = self.panel_rect.y + 70
        details_height = 56
        body_height = max(340, self.panel_rect.height - 112 - details_height)

        left_x = self.panel_rect.x + self.panel_padding
        center_x = left_x + left_width + self.column_gap
        equipment_x = center_x + center_width + self.column_gap
        quest_x = equipment_x + side_width + self.column_gap

        total_width = quest_x + side_width - left_x
        available_width = self.panel_rect.width - self.panel_padding * 2
        if total_width > available_width:
            overflow = total_width - available_width
            center_width = max(220, center_width - overflow)
            equipment_x = center_x + center_width + self.column_gap
            quest_x = equipment_x + side_width + self.column_gap

        self.left_panel = pygame.Rect(left_x, content_top, left_width, body_height)
        self.center_panel = pygame.Rect(center_x, content_top, center_width, body_height)
        self.equipment_panel = pygame.Rect(equipment_x, content_top, side_width, body_height)
        self.quest_panel = pygame.Rect(quest_x, content_top, side_width, body_height)
        self.details_panel = pygame.Rect(
            center_x,
            content_top + body_height + 10,
            self.panel_rect.right - self.panel_padding - center_x,
            details_height,
        )

        hotbar_width = HOTBAR_SIZE * self.inventory_slot_size
        hotbar_width += (HOTBAR_SIZE - 1) * self.inventory_gap + 16
        self.hotbar_panel = pygame.Rect(
            self.center_panel.centerx - hotbar_width // 2,
            self.center_panel.y + 42,
            hotbar_width,
            72 if compact else 92,
        )
        self.hotbar_origin = (self.hotbar_panel.x + 8, self.hotbar_panel.y + 30)
        self.inventory_origin = (self.center_panel.x + 16, self.hotbar_panel.bottom + 24)
        self.quest_origin = (self.quest_panel.x + 8, self.quest_panel.y + 60)

        equipment_slot_width = self.equipment_panel.width - 16
        equipment_slot_height = 32
        equipment_slot_x = self.equipment_panel.x + 8
        equipment_slot_y = self.equipment_panel.y + 54
        equipment_spacing = 10
        self.equipment_slots = [
            (EquipSlot.HELMET, pygame.Rect(equipment_slot_x, equipment_slot_y + (equipment_slot_height + equipment_spacing) * 0, equipment_slot_width, equipment_slot_height)),
            (EquipSlot.CHEST, pygame.Rect(equipment_slot_x, equipment_slot_y + (equipment_slot_height + equipment_spacing) * 1, equipment_slot_width, equipment_slot_height)),
            (EquipSlot.BOOTS, pygame.Rect(equipment_slot_x, equipment_slot_y + (equipment_slot_height + equipment_spacing) * 2, equipment_slot_width, equipment_slot_height)),
            (EquipSlot.WEAPON, pygame.Rect(equipment_slot_x, equipment_slot_y + (equipment_slot_height + equipment_spacing) * 3, equipment_slot_width, equipment_slot_height)),
            (EquipSlot.ACCESSORY_1, pygame.Rect(equipment_slot_x, equipment_slot_y + (equipment_slot_height + equipment_spacing) * 4, equipment_slot_width, equipment_slot_height)),
            (EquipSlot.ACCESSORY_2, pygame.Rect(equipment_slot_x, equipment_slot_y + (equipment_slot_height + equipment_spacing) * 5, equipment_slot_width, equipment_slot_height)),
        ]

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_i):
                self.app.set_scene(self.game_scene)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_left_button_down(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event.pos, event.buttons)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._handle_left_button_up(event.pos)

    def _handle_left_button_down(self, mouse_pos):
        self._build_layout()
        slot = self._slot_at(mouse_pos)
        self.pressed_slot = slot
        self.drag_source = None
        self.drag_start_pos = None
        self.dragging = False

        if slot is None:
            return

        kind, index = slot
        if kind in ("inventory", "hotbar", "quest"):
            stack = self._get_slot_stack(kind, index)
            if stack is None:
                return
            self.drag_start_pos = mouse_pos
        return

    def _handle_mouse_motion(self, mouse_pos, buttons):
        if self.pressed_slot is None or self.drag_start_pos is None or not buttons[0] or self.dragging:
            return

        dx = mouse_pos[0] - self.drag_start_pos[0]
        dy = mouse_pos[1] - self.drag_start_pos[1]
        if dx * dx + dy * dy >= self.drag_threshold * self.drag_threshold:
            self.drag_source = self.pressed_slot
            self.dragging = True

    def _handle_left_button_up(self, mouse_pos):
        target = self._slot_at(mouse_pos)
        source = self.drag_source
        pressed_slot = self.pressed_slot

        if self.dragging and source is None:
            self.pressed_slot = None
            self.drag_start_pos = None
            self.dragging = False
            return

        if not self.dragging and pressed_slot is None:
            return

        if self.dragging:
            movable_kinds = {"inventory", "hotbar", "quest"}
            if target is not None and target[:2] != source[:2] and target[0] in movable_kinds:
                if self._transfer_between_slots(source, target):
                    self.selected_slot = target
                else:
                    self.selected_slot = source
            else:
                self.selected_slot = source
        else:
            if target is None or target != pressed_slot:
                self.selected_slot = None
            elif target[0] == "inventory":
                self._handle_inventory_click(target[1])
            elif target[0] == "hotbar":
                self._handle_hotbar_click(target[1])
            elif target[0] == "quest":
                self._handle_quest_click(target[1])
            elif target[0] == "equipment":
                self._handle_equipment_click(target[1])

        self.pressed_slot = None
        self.drag_source = None
        self.drag_start_pos = None
        self.dragging = False

    def _handle_inventory_click(self, inventory_index):
        stack = self.player.inventory.get_stack_at(inventory_index)
        if self.selected_slot is None:
            if stack is not None:
                self.selected_slot = ("inventory", inventory_index)
            return

        selected_kind, selected_index = self.selected_slot
        if selected_kind == "inventory" and selected_index == inventory_index:
            self.selected_slot = None
            return

        if stack is not None:
            self.selected_slot = ("inventory", inventory_index)
            return

        self.selected_slot = None

    def _handle_hotbar_click(self, hotbar_index):
        stack = self.player.get_hotbar_stack(hotbar_index)
        if self.selected_slot is None:
            if stack is not None:
                self.selected_slot = ("hotbar", hotbar_index)
            return

        selected_kind, selected_index = self.selected_slot
        if selected_kind == "hotbar" and selected_index == hotbar_index:
            self.selected_slot = None
            return

        if stack is not None:
            self.selected_slot = ("hotbar", hotbar_index)
            return

        self.selected_slot = None

    def _handle_quest_click(self, quest_index):
        stack = self.player.quest_inventory.get_stack_at(quest_index)
        if self.selected_slot is None:
            if stack is not None:
                self.selected_slot = ("quest", quest_index)
            return

        selected_kind, selected_index = self.selected_slot
        if selected_kind == "quest" and selected_index == quest_index:
            self.selected_slot = None
            return

        if stack is not None:
            self.selected_slot = ("quest", quest_index)
            return

        self.selected_slot = None

    def _handle_equipment_click(self, equip_slot):
        if self.selected_slot is not None and self.selected_slot[0] == "inventory":
            inventory_index = self.selected_slot[1]
            if self.player.equip_inventory_slot(inventory_index, equip_slot):
                self._set_message(self.localizer.t("ui.inventory.equip_success"))
                self.selected_slot = None
            else:
                self._set_message(self.localizer.t("ui.inventory.equip_failed"))
            return

        if self.player.equipment.get(equip_slot) is not None:
            if self.player.unequip_to_inventory(equip_slot):
                self._set_message(self.localizer.t("ui.inventory.unequip_success"))
                self.selected_slot = None
            else:
                self._set_message(self.localizer.t("ui.inventory.inventory_full"))

    def _set_message(self, text):
        self.message = text
        self.message_timer = 2.0

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0.0:
                self.message = ""

    def draw(self):
        self._build_layout()
        self.game_scene.draw()

        screen_width, screen_height = self.app.get_screen_size()
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.app.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.panel_rect, border_radius=14)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.panel_rect, width=2, border_radius=14)

        title = self.title_font.render(self.localizer.t("ui.inventory.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, (self.panel_rect.x + 28, self.panel_rect.y + 12))

        self._draw_header_currencies()

        self._draw_character_panel()
        self._draw_inventory_grid()
        self._draw_hotbar_panel()
        self._draw_equipment_panel()
        self._draw_quest_panel()
        self._draw_details_panel()
        self._draw_drag_preview()

        if self.message:
            message = self.text_font.render(self.message, True, (255, 220, 120))
            self.app.screen.blit(message, message.get_rect(center=(screen_width // 2, screen_height - 22)))
        self._draw_header_currency_tooltip()

    def _draw_header_currencies(self):
        self.header_currency_targets = []
        entries = [
            ("coin", self.player.coins),
            ("knowledge_shard", self.player.knowledge_shards),
        ]
        right_edge = self.panel_rect.right - 28
        top_y = self.panel_rect.y + 18
        row_height = 28
        icon_size = 20
        gap = 8

        for index, (item_id, amount) in enumerate(entries):
            icon = get_item_icon(item_id, (icon_size, icon_size))
            amount_text = self.text_font.render(str(amount), True, COLORS["WHITE"])
            row_y = top_y + index * row_height
            amount_x = right_edge - amount_text.get_width()
            self.app.screen.blit(amount_text, (amount_x, row_y))

            if icon is not None:
                icon_rect = icon.get_rect(midright=(amount_x - gap, row_y + amount_text.get_height() // 2))
                self.app.screen.blit(icon, icon_rect.topleft)
                self.header_currency_targets.append((icon_rect.inflate(6, 6), item_id))

    def _draw_header_currency_tooltip(self):
        mouse_pos = pygame.mouse.get_pos()
        hovered_item_id = None
        for rect, item_id in self.header_currency_targets:
            if rect.collidepoint(mouse_pos):
                hovered_item_id = item_id
                break
        if hovered_item_id is None:
            return

        definition = get_item_definition(hovered_item_id)
        if definition is None:
            return
        label = definition.localized_name()
        text = self.small_font.render(label, True, COLORS["WHITE"])
        padding_x = 10
        padding_y = 6
        tooltip_rect = pygame.Rect(
            mouse_pos[0] + 14,
            mouse_pos[1] + 14,
            text.get_width() + padding_x * 2,
            text.get_height() + padding_y * 2,
        )
        screen_width, screen_height = self.app.get_screen_size()
        if tooltip_rect.right > screen_width - 8:
            tooltip_rect.x = mouse_pos[0] - tooltip_rect.width - 14
        if tooltip_rect.bottom > screen_height - 8:
            tooltip_rect.y = mouse_pos[1] - tooltip_rect.height - 14

        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], tooltip_rect, border_radius=8)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], tooltip_rect, width=1, border_radius=8)
        self.app.screen.blit(text, (tooltip_rect.x + padding_x, tooltip_rect.y + padding_y))

    def _draw_character_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.left_panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.left_panel, width=2, border_radius=12)
        self._draw_panel_title(self.left_panel, self.localizer.t("ui.inventory.character"))

        body_rect = pygame.Rect(self.left_panel.centerx - 30, self.left_panel.y + 72, 60, 90)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_SELECTED"], body_rect, border_radius=10)
        pygame.draw.rect(self.app.screen, COLORS["WHITE"], body_rect, width=2, border_radius=10)

        stats = self.player.get_effective_stats()
        stat_lines = [
            self.localizer.t("ui.progression.level", level=self.player.level),
            self.localizer.t("ui.progression.xp", xp=self.player.xp, required=self.player.get_xp_to_next_level()),
            self.localizer.t("ui.progression.skill_points", points=self.player.skill_points),
            f"{self.localizer.t('ui.inventory.stat_hp')}: {int(self.player.health)}/{self.player.get_max_health()}",
            f"{self.localizer.t('ui.inventory.stat_st')}: {int(self.player.stamina)}/{self.player.get_max_stamina()}",
            f"{self.localizer.t('ui.inventory.stat_atk')}: {stats.attack}",
            f"{self.localizer.t('ui.inventory.stat_def')}: {stats.defense}",
            f"{self.localizer.t('ui.inventory.stat_spd')}: {stats.speed}",
        ]
        stats_start_y = body_rect.bottom + 14
        for index, line in enumerate(stat_lines):
            text = self.stats_font.render(line, True, COLORS["WHITE"])
            self.app.screen.blit(text, (self.left_panel.x + 18, stats_start_y + index * 24))

    def _draw_hotbar_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.hotbar_panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.hotbar_panel, width=2, border_radius=12)
        label = self.small_font.render(self.localizer.t("ui.inventory.hotbar"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(label, (self.hotbar_panel.x + 12, self.hotbar_panel.y + 10))

        for index in range(HOTBAR_SIZE):
            rect = self._hotbar_rect(index)
            selected = self.selected_slot == ("hotbar", index)
            active = index == self.player.selected_hotbar_index
            stack = self.player.get_hotbar_stack(index)
            if self.dragging and self.drag_source == ("hotbar", index):
                stack = None

            fill = COLORS["UI_PANEL"] if active else COLORS["UI_SLOT"]
            border = COLORS["UI_SLOT_SELECTED"] if selected or active else COLORS["UI_SLOT_BORDER"]
            pygame.draw.rect(self.app.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

            key_label = self.small_font.render(str(index + 1), True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(key_label, (rect.x + 3, rect.y + 2))

            if stack is not None:
                self._draw_stack_label(stack, rect)

    def _draw_inventory_grid(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.center_panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.center_panel, width=2, border_radius=12)
        self._draw_panel_title(self.center_panel, self.localizer.t("ui.inventory.backpack"))

        for row in range(self.inventory_rows):
            for col in range(self.inventory_columns):
                index = row * self.inventory_columns + col
                if index >= self.inventory_slot_count:
                    continue

                rect = self._inventory_rect(row, col)
                selected = self.selected_slot == ("inventory", index)
                stack = self.player.inventory.get_stack_at(index)
                if self.dragging and self.drag_source == ("inventory", index):
                    stack = None
                border = COLORS["UI_SLOT_SELECTED"] if selected else COLORS["UI_SLOT_BORDER"]
                pygame.draw.rect(self.app.screen, COLORS["UI_SLOT"], rect, border_radius=8)
                pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

                index_label = self.small_font.render(str(index + 1), True, COLORS["UI_TEXT_DIM"])
                self.app.screen.blit(index_label, (rect.x + 3, rect.y + 2))

                if stack is not None:
                    self._draw_stack_label(stack, rect)

    def _draw_equipment_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.equipment_panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.equipment_panel, width=2, border_radius=12)
        self._draw_panel_title(self.equipment_panel, self.localizer.t("ui.inventory.equipment"))

        for slot, rect in self.equipment_slots:
            stack = self.player.equipment.get(slot)
            border = COLORS["EQUIP_SLOT_FILLED"] if stack is not None else COLORS["EQUIP_SLOT"]
            pygame.draw.rect(self.app.screen, COLORS["UI_SLOT"], rect, border_radius=8)
            pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

            title_text = self.small_font.render(self._equipment_slot_label(slot), True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(title_text, (rect.x + 4, rect.y + 2))

            if stack is not None:
                self._draw_stack_label(stack, rect)

    def _draw_quest_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.quest_panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.quest_panel, width=2, border_radius=12)
        self._draw_panel_title(self.quest_panel, self.localizer.t("ui.inventory.quest_items"))

        for row in range(self.QUEST_ROWS):
            for col in range(self.QUEST_COLUMNS):
                index = row * self.QUEST_COLUMNS + col
                if index >= self.quest_slot_count:
                    continue

                rect = self._quest_rect(row, col)
                selected = self.selected_slot == ("quest", index)
                stack = self.player.quest_inventory.get_stack_at(index)
                if self.dragging and self.drag_source == ("quest", index):
                    stack = None
                border = COLORS["UI_SLOT_SELECTED"] if selected else COLORS["UI_SLOT_BORDER"]
                pygame.draw.rect(self.app.screen, COLORS["UI_SLOT"], rect, border_radius=8)
                pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

                if stack is not None:
                    self._draw_stack_label(stack, rect)

    def _draw_details_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.details_panel, border_radius=10)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.details_panel, width=1, border_radius=10)

        stack = self._get_selected_stack()
        if stack is None:
            text = self.text_font.render(self.localizer.t("ui.inventory.select_item_hint"), True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(text, (self.details_panel.x + 14, self.details_panel.y + 14))
            return

        name = self.text_font.render(stack.name, True, COLORS["WHITE"])
        self.app.screen.blit(name, (self.details_panel.x + 14, self.details_panel.y + 4))

        detail = stack.description or stack.kind.value
        detail_text = self.small_font.render(detail, True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(detail_text, (self.details_panel.x + 14, self.details_panel.y + 28))

    def _draw_panel_title(self, panel_rect, text):
        available_width = panel_rect.width - 20
        font = self.section_font if self.section_font.size(text)[0] <= available_width else self.panel_title_font
        label = font.render(text, True, COLORS["WHITE"])
        self.app.screen.blit(label, (panel_rect.x + 10, panel_rect.y + 14))

    def _draw_stack_label(self, stack, rect):
        icon = get_item_icon(stack.definition, (rect.width - 12, rect.height - 12))
        if icon is not None:
            self.app.screen.blit(icon, icon.get_rect(center=rect.center))
        else:
            item_label = self.text_font.render(stack.name[:2].upper(), True, COLORS["WHITE"])
            self.app.screen.blit(item_label, item_label.get_rect(center=rect.center))
        if stack.quantity > 1:
            qty = self.small_font.render(str(stack.quantity), True, COLORS["WHITE"])
            self.app.screen.blit(qty, (rect.right - qty.get_width() - 4, rect.bottom - qty.get_height() - 2))

    def _draw_drag_preview(self):
        if not self.dragging or self.drag_source is None:
            return

        stack = self._get_slot_stack(*self.drag_source)
        if stack is None:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        rect = pygame.Rect(
            mouse_x - self.inventory_slot_size // 2,
            mouse_y - self.inventory_slot_size // 2,
            self.inventory_slot_size,
            self.inventory_slot_size,
        )
        preview = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        preview.fill((60, 60, 76, 220))
        pygame.draw.rect(preview, (120, 180, 255, 240), preview.get_rect(), width=2, border_radius=8)

        icon = get_item_icon(stack.definition, (rect.width - 12, rect.height - 12))
        if icon is not None:
            preview.blit(icon, icon.get_rect(center=preview.get_rect().center))
        else:
            key_label = self.text_font.render(stack.name[:2].upper(), True, COLORS["WHITE"])
            preview.blit(key_label, key_label.get_rect(center=preview.get_rect().center))
        if stack.quantity > 1:
            qty = self.small_font.render(str(stack.quantity), True, COLORS["WHITE"])
            preview.blit(qty, (rect.width - qty.get_width() - 4, rect.height - qty.get_height() - 2))

        self.app.screen.blit(preview, rect.topleft)

    def _get_selected_stack(self):
        if self.selected_slot is None:
            return None

        selected_kind, selected_index = self.selected_slot
        if selected_kind == "inventory":
            return self.player.inventory.get_stack_at(selected_index)
        if selected_kind == "hotbar":
            return self.player.get_hotbar_stack(selected_index)
        if selected_kind == "quest":
            return self.player.quest_inventory.get_stack_at(selected_index)
        return None

    def _slot_at(self, mouse_pos):
        hotbar_index = self._hotbar_index_at(mouse_pos)
        if hotbar_index is not None:
            return ("hotbar", hotbar_index)

        inventory_index = self._inventory_index_at(mouse_pos)
        if inventory_index is not None:
            return ("inventory", inventory_index)

        quest_index = self._quest_index_at(mouse_pos)
        if quest_index is not None:
            return ("quest", quest_index)

        equipment_slot = self._equipment_slot_at(mouse_pos)
        if equipment_slot is not None:
            return ("equipment", equipment_slot[0])

        return None

    def _get_slot_stack(self, kind, index):
        if kind == "inventory":
            return self.player.inventory.get_stack_at(index)
        if kind == "hotbar":
            return self.player.get_hotbar_stack(index)
        if kind == "quest":
            return self.player.quest_inventory.get_stack_at(index)
        if kind == "equipment":
            return self.player.equipment.get(index)
        return None

    def _set_slot_stack(self, kind, index, stack):
        if kind == "inventory":
            return self.player.inventory.set_stack_at(index, stack)
        if kind == "hotbar":
            return self.player.set_hotbar_slot(index, stack)
        if kind == "quest":
            if stack is not None and stack.kind != ItemKind.QUEST:
                return False
            return self.player.quest_inventory.set_stack_at(index, stack)
        return False

    def _clear_slot(self, kind, index):
        if kind == "inventory":
            return self.player.inventory.clear_slot(index)
        if kind == "hotbar":
            return self.player.clear_hotbar_slot(index)
        if kind == "quest":
            return self.player.quest_inventory.clear_slot(index)
        return None

    def _transfer_between_slots(self, source, target):
        source_kind, source_index = source
        target_kind, target_index = target
        if source_kind == target_kind and source_index == target_index:
            return False

        source_stack = self._get_slot_stack(source_kind, source_index)
        target_stack = self._get_slot_stack(target_kind, target_index)
        if source_stack is None:
            return False

        if "quest" in (source_kind, target_kind):
            if source_kind != target_kind or source_stack.kind != ItemKind.QUEST:
                self._set_message(self.localizer.t("ui.inventory.quest_cannot_move"))
                return False

        if target_stack is None:
            if not self._set_slot_stack(target_kind, target_index, source_stack):
                return False
            self._clear_slot(source_kind, source_index)
            return True

        if source_stack.can_stack_with(target_stack):
            transferred = min(source_stack.quantity, target_stack.available_space())
            if transferred <= 0:
                return False
            target_stack.quantity += transferred
            source_stack.quantity -= transferred
            if source_stack.quantity <= 0:
                self._clear_slot(source_kind, source_index)
            return True

        if not self._set_slot_stack(source_kind, source_index, target_stack):
            return False
        if not self._set_slot_stack(target_kind, target_index, source_stack):
            self._set_slot_stack(source_kind, source_index, source_stack)
            return False
        return True

    def _inventory_rect(self, row, col):
        x = self.inventory_origin[0] + col * (self.inventory_slot_size + self.inventory_gap)
        y = self.inventory_origin[1] + row * (self.inventory_slot_size + self.inventory_gap)
        return pygame.Rect(x, y, self.inventory_slot_size, self.inventory_slot_size)

    def _quest_rect(self, row, col):
        x = self.quest_origin[0] + col * (self.inventory_slot_size + self.inventory_gap)
        y = self.quest_origin[1] + row * (self.inventory_slot_size + self.inventory_gap)
        return pygame.Rect(x, y, self.inventory_slot_size, self.inventory_slot_size)

    def _hotbar_rect(self, index):
        x = self.hotbar_origin[0] + index * (self.inventory_slot_size + self.inventory_gap)
        return pygame.Rect(x, self.hotbar_origin[1], self.inventory_slot_size, self.inventory_slot_size)

    def _inventory_index_at(self, mouse_pos):
        for row in range(self.inventory_rows):
            for col in range(self.inventory_columns):
                index = row * self.inventory_columns + col
                if index >= self.inventory_slot_count:
                    continue
                if self._inventory_rect(row, col).collidepoint(mouse_pos):
                    return index
        return None

    def _quest_index_at(self, mouse_pos):
        for row in range(self.QUEST_ROWS):
            for col in range(self.QUEST_COLUMNS):
                index = row * self.QUEST_COLUMNS + col
                if index >= self.quest_slot_count:
                    continue
                if self._quest_rect(row, col).collidepoint(mouse_pos):
                    return index
        return None

    def _hotbar_index_at(self, mouse_pos):
        for index in range(HOTBAR_SIZE):
            if self._hotbar_rect(index).collidepoint(mouse_pos):
                return index
        return None

    def _equipment_slot_at(self, mouse_pos):
        for slot in self.equipment_slots:
            if slot[1].collidepoint(mouse_pos):
                return slot
        return None

    def _equipment_slot_label(self, slot):
        mapping = {
            EquipSlot.HELMET: "ui.inventory.slot_helmet",
            EquipSlot.CHEST: "ui.inventory.slot_chest",
            EquipSlot.BOOTS: "ui.inventory.slot_boots",
            EquipSlot.WEAPON: "ui.inventory.slot_weapon",
            EquipSlot.ACCESSORY_1: "ui.inventory.slot_accessory_1",
            EquipSlot.ACCESSORY_2: "ui.inventory.slot_accessory_2",
        }
        return self.localizer.t(mapping.get(slot, "ui.inventory.equipment"))
