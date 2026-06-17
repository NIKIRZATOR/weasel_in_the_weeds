import pygame
from math import ceil

from game.items.types import EquipSlot
from game.scenes.base import Scene
from settings import (
    COLORS,
    HOTBAR_SIZE,
    INVENTORY_COLUMNS,
    INVENTORY_ROWS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class InventoryScene(Scene):
    def __init__(self, app, game_scene):
        self.app = app
        self.game_scene = game_scene
        self.player = game_scene.player
        self.title_font = pygame.font.Font(None, 62)
        self.section_font = pygame.font.Font(None, 30)
        self.text_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.message = ""
        self.message_timer = 0.0
        self.selected_slot = None
        self.drag_source = None
        self.drag_start_pos = None
        self.dragging = False
        self.drag_threshold = 6
        self._build_layout()

    def _build_layout(self):
        self.panel_rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80)
        self.left_panel = pygame.Rect(60, 110, 200, 410)
        self.center_panel = pygame.Rect(280, 110, 320, 410)
        self.right_panel = pygame.Rect(620, 110, 120, 410)
        self.details_panel = pygame.Rect(280, 530, 460, 50)

        self.inventory_slot_size = 48
        self.inventory_gap = 8
        self.hotbar_panel = pygame.Rect(296, 154, 248, 92)
        self.hotbar_origin = (312, 188)
        self.inventory_origin = (310, 270)
        self.inventory_columns = INVENTORY_COLUMNS
        self.inventory_slot_count = self.player.inventory.capacity
        self.inventory_rows = min(
            INVENTORY_ROWS,
            max(1, ceil(self.inventory_slot_count / self.inventory_columns)),
        )

        self.equipment_slots = [
            (EquipSlot.HELMET, pygame.Rect(640, 170, 70, 36), "Helmet"),
            (EquipSlot.CHEST, pygame.Rect(640, 220, 70, 36), "Chest"),
            (EquipSlot.BOOTS, pygame.Rect(640, 270, 70, 36), "Boots"),
            (EquipSlot.WEAPON, pygame.Rect(640, 320, 70, 36), "Weapon"),
            (EquipSlot.ACCESSORY_1, pygame.Rect(640, 370, 70, 36), "Acc 1"),
            (EquipSlot.ACCESSORY_2, pygame.Rect(640, 420, 70, 36), "Acc 2"),
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
        slot = self._slot_at(mouse_pos)
        self.drag_source = None
        self.drag_start_pos = None
        self.dragging = False

        if slot is None:
            self.selected_slot = None
            return

        kind, index = slot
        if kind in ("inventory", "hotbar"):
            stack = self._get_slot_stack(kind, index)
            if stack is None:
                self.selected_slot = None
                return
            self.selected_slot = slot
            self.drag_source = slot
            self.drag_start_pos = mouse_pos
            return

        if kind == "equipment":
            self._handle_equipment_click(index)

    def _handle_mouse_motion(self, mouse_pos, buttons):
        if self.drag_source is None or self.drag_start_pos is None or not buttons[0] or self.dragging:
            return

        dx = mouse_pos[0] - self.drag_start_pos[0]
        dy = mouse_pos[1] - self.drag_start_pos[1]
        if dx * dx + dy * dy >= self.drag_threshold * self.drag_threshold:
            self.dragging = True

    def _handle_left_button_up(self, mouse_pos):
        if self.drag_source is None:
            return

        source = self.drag_source
        target = self._slot_at(mouse_pos)

        if self.dragging:
            if target is not None and target[:2] != source[:2] and target[0] in ("inventory", "hotbar"):
                if self._transfer_between_slots(source, target):
                    self.selected_slot = target
                else:
                    self.selected_slot = source
            elif target is not None and target[0] == "equipment":
                self.selected_slot = source
            else:
                self.selected_slot = source
        else:
            if target is None:
                self.selected_slot = None
            elif target[0] == "inventory":
                self._handle_inventory_click(target[1])
            elif target[0] == "hotbar":
                self._handle_hotbar_click(target[1])
            elif target[0] == "equipment":
                self._handle_equipment_click(target[1])

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
        if selected_kind == "inventory":
            if selected_index == inventory_index:
                self.selected_slot = None
                return
            self.player.inventory.swap_slots(selected_index, inventory_index)
            self.selected_slot = ("inventory", inventory_index)
            return

        if selected_kind == "hotbar":
            if self.player.swap_inventory_and_hotbar(inventory_index, selected_index):
                self.selected_slot = ("inventory", inventory_index)
            else:
                self._set_message("Не удалось переместить предмет")

    def _handle_hotbar_click(self, hotbar_index):
        stack = self.player.get_hotbar_stack(hotbar_index)
        if self.selected_slot is None:
            if stack is not None:
                self.selected_slot = ("hotbar", hotbar_index)
            return

        selected_kind, selected_index = self.selected_slot
        if selected_kind == "hotbar":
            if selected_index == hotbar_index:
                self.selected_slot = None
                return
            self.player.swap_hotbar_slots(selected_index, hotbar_index)
            self.selected_slot = ("hotbar", hotbar_index)
            return

        if selected_kind == "inventory":
            if self.player.swap_inventory_and_hotbar(selected_index, hotbar_index):
                self.selected_slot = ("hotbar", hotbar_index)
            else:
                self._set_message("Не удалось переместить предмет")

    def _handle_equipment_click(self, equip_slot):
        if self.selected_slot is not None and self.selected_slot[0] == "inventory":
            inventory_index = self.selected_slot[1]
            if self.player.equip_inventory_slot(inventory_index, equip_slot):
                self._set_message("Предмет экипирован")
                self.selected_slot = None
            else:
                self._set_message("Нельзя экипировать в этот слот")
            return

        if self.player.equipment.get(equip_slot) is not None:
            if self.player.unequip_to_inventory(equip_slot):
                self._set_message("Предмет снят")
                self.selected_slot = None
            else:
                self._set_message("Инвентарь переполнен")

    def _set_message(self, text):
        self.message = text
        self.message_timer = 2.0

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0.0:
                self.message = ""

    def draw(self):
        self.game_scene.draw()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.app.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.panel_rect, border_radius=14)
        pygame.draw.rect(
            self.app.screen,
            COLORS["UI_SLOT_BORDER"],
            self.panel_rect,
            width=2,
            border_radius=14,
        )

        title = self.title_font.render("Инвентарь", True, COLORS["WHITE"])
        self.app.screen.blit(title, (70, 55))
        hint = self.text_font.render("Esc / I - закрыть", True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 72, 60))

        self._draw_character_panel()
        self._draw_inventory_grid()
        self._draw_hotbar_panel()
        self._draw_equipment_panel()
        self._draw_details_panel()
        self._draw_drag_preview()

        if self.message:
            message = self.text_font.render(self.message, True, (255, 220, 120))
            self.app.screen.blit(
                message,
                message.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 22)),
            )

    def _draw_character_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.left_panel, border_radius=12)
        pygame.draw.rect(
            self.app.screen,
            COLORS["UI_SLOT_BORDER"],
            self.left_panel,
            width=2,
            border_radius=12,
        )
        label = self.section_font.render("Персонаж", True, COLORS["WHITE"])
        self.app.screen.blit(label, (self.left_panel.x + 16, self.left_panel.y + 14))

        body_rect = pygame.Rect(self.left_panel.centerx - 30, self.left_panel.y + 85, 60, 90)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_SELECTED"], body_rect, border_radius=10)
        pygame.draw.rect(self.app.screen, COLORS["WHITE"], body_rect, width=2, border_radius=10)

        stats = self.player.get_effective_stats()
        stat_lines = [
            f"HP: {int(self.player.health)}/{self.player.get_max_health()}",
            f"ST: {int(self.player.stamina)}/{self.player.get_max_stamina()}",
            f"ATK: {stats.attack}",
            f"DEF: {stats.defense}",
            f"SPD: {stats.speed}",
            f"Coins: {self.player.coins}",
        ]
        for index, line in enumerate(stat_lines):
            text = self.text_font.render(line, True, COLORS["WHITE"])
            self.app.screen.blit(text, (self.left_panel.x + 18, self.left_panel.y + 200 + index * 30))

    def _draw_hotbar_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.hotbar_panel, border_radius=12)
        pygame.draw.rect(
            self.app.screen,
            COLORS["UI_SLOT_BORDER"],
            self.hotbar_panel,
            width=2,
            border_radius=12,
        )
        label = self.small_font.render("Хотбар", True, COLORS["UI_TEXT_DIM"])
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
        pygame.draw.rect(
            self.app.screen,
            COLORS["UI_SLOT_BORDER"],
            self.center_panel,
            width=2,
            border_radius=12,
        )
        label = self.section_font.render("Инвентарь", True, COLORS["WHITE"])
        self.app.screen.blit(label, (self.center_panel.x + 16, self.center_panel.y + 14))

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
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.right_panel, border_radius=12)
        pygame.draw.rect(
            self.app.screen,
            COLORS["UI_SLOT_BORDER"],
            self.right_panel,
            width=2,
            border_radius=12,
        )
        label = self.section_font.render("Надето", True, COLORS["WHITE"])
        self.app.screen.blit(label, (self.right_panel.x + 12, self.right_panel.y + 14))

        for slot, rect, title in self.equipment_slots:
            stack = self.player.equipment.get(slot)
            border = COLORS["EQUIP_SLOT_FILLED"] if stack is not None else COLORS["EQUIP_SLOT"]
            pygame.draw.rect(self.app.screen, COLORS["UI_SLOT"], rect, border_radius=8)
            pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

            title_text = self.small_font.render(title, True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(title_text, (rect.x + 4, rect.y + 2))

            if stack is not None:
                item_text = self.small_font.render(stack.name[:8], True, COLORS["WHITE"])
                self.app.screen.blit(item_text, item_text.get_rect(center=rect.center))

    def _draw_details_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.details_panel, border_radius=10)
        pygame.draw.rect(
            self.app.screen,
            COLORS["UI_SLOT_BORDER"],
            self.details_panel,
            width=1,
            border_radius=10,
        )

        stack = self._get_selected_stack()
        if stack is None:
            text = self.text_font.render(
                "Выберите предмет, чтобы увидеть описание.",
                True,
                COLORS["UI_TEXT_DIM"],
            )
            self.app.screen.blit(text, (self.details_panel.x + 14, self.details_panel.y + 14))
            return

        name = self.text_font.render(stack.name, True, COLORS["WHITE"])
        self.app.screen.blit(name, (self.details_panel.x + 14, self.details_panel.y + 4))

        detail = stack.definition.description or stack.kind.value
        detail_text = self.small_font.render(detail, True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(detail_text, (self.details_panel.x + 14, self.details_panel.y + 28))

    def _draw_stack_label(self, stack, rect):
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
        return None

    def _slot_at(self, mouse_pos):
        hotbar_index = self._hotbar_index_at(mouse_pos)
        if hotbar_index is not None:
            return ("hotbar", hotbar_index)

        inventory_index = self._inventory_index_at(mouse_pos)
        if inventory_index is not None:
            return ("inventory", inventory_index)

        equipment_slot = self._equipment_slot_at(mouse_pos)
        if equipment_slot is not None:
            return ("equipment", equipment_slot[0])

        return None

    def _get_slot_stack(self, kind, index):
        if kind == "inventory":
            return self.player.inventory.get_stack_at(index)
        if kind == "hotbar":
            return self.player.get_hotbar_stack(index)
        if kind == "equipment":
            return self.player.equipment.get(index)
        return None

    def _set_slot_stack(self, kind, index, stack):
        if kind == "inventory":
            return self.player.inventory.set_stack_at(index, stack)
        if kind == "hotbar":
            return self.player.set_hotbar_slot(index, stack)
        return False

    def _clear_slot(self, kind, index):
        if kind == "inventory":
            return self.player.inventory.clear_slot(index)
        if kind == "hotbar":
            return self.player.clear_hotbar_slot(index)
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
