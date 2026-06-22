from __future__ import annotations

import pygame

from game.crafting import get_recipe_definitions
from game.items import create_item_stack, get_item_definition, get_item_icon
from game.localization import get_localizer
from game.scenes.base import Scene
from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH


class CraftingScene(Scene):
    def __init__(self, app, game_scene):
        self.app = app
        self.game_scene = game_scene
        self.player = game_scene.player
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 56)
        self.section_font = pygame.font.Font(None, 30)
        self.text_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.message = ""
        self.message_timer = 0.0
        self.active_category = "all"
        self.selected_recipe_id = None
        self.category_buttons = []
        self.category_scroll_area = None
        self.category_left_button = None
        self.category_right_button = None
        self.category_scroll_offset = 0
        self.category_content_width = 0
        self.recipe_rows = []
        self.action_button = None
        self._layout_size = None
        self._build_layout()
        self._ensure_selected_recipe()

    def _build_layout(self):
        screen_width, screen_height = self.app.get_screen_size()
        layout_size = (screen_width, screen_height)
        if self._layout_size == layout_size:
            return
        self._layout_size = layout_size

        panel_width = min(SCREEN_WIDTH + 320, screen_width - 40)
        panel_height = min(SCREEN_HEIGHT + 120, screen_height - 40)
        self.panel_rect = pygame.Rect(
            max(20, (screen_width - panel_width) // 2),
            max(20, (screen_height - panel_height) // 2),
            panel_width,
            panel_height,
        )

        panel_padding = 24
        content_top = self.panel_rect.y + 74
        content_height = self.panel_rect.height - 108
        left_width = int(self.panel_rect.width * 0.42)
        right_width = self.panel_rect.width - panel_padding * 2 - left_width - 16

        self.left_panel = pygame.Rect(self.panel_rect.x + panel_padding, content_top, left_width, content_height)
        self.right_panel = pygame.Rect(self.left_panel.right + 16, content_top, right_width, content_height)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_k):
                    self.app.set_scene(self.game_scene)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._move_selection(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._move_selection(1)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._switch_category(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._switch_category(1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._perform_primary_action()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_click(event.pos)
                elif event.button == 4:
                    self._scroll_categories(-120)
                elif event.button == 5:
                    self._scroll_categories(120)

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0.0:
                self.message = ""

    def draw(self):
        self._build_layout()
        self._ensure_selected_recipe()
        self.game_scene.draw()

        screen_width, screen_height = self.app.get_screen_size()
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.app.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"], self.panel_rect, border_radius=16)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.panel_rect, width=2, border_radius=16)

        title = self.title_font.render(self.localizer.t("ui.crafting.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, (self.panel_rect.x + 24, self.panel_rect.y + 14))
        hint = self.text_font.render(self.localizer.t("ui.crafting.close_hint"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(hint, (self.panel_rect.right - hint.get_width() - 24, self.panel_rect.y + 24))

        self._draw_left_panel()
        self._draw_right_panel()

        if self.message:
            text = self.text_font.render(self.message, True, (255, 220, 120))
            self.app.screen.blit(text, text.get_rect(center=(screen_width // 2, self.panel_rect.bottom - 18)))

    def _draw_left_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.left_panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.left_panel, width=2, border_radius=12)

        self.category_buttons = []
        self.category_content_width = 0
        category_y = self.left_panel.y + 16
        arrow_size = 28
        gap = 8
        scroll_needed = self._category_scroll_needed()
        if scroll_needed:
            self.category_left_button = pygame.Rect(self.left_panel.x + 14, category_y, arrow_size, arrow_size)
            self.category_right_button = pygame.Rect(self.left_panel.right - 14 - arrow_size, category_y, arrow_size, arrow_size)
            self.category_scroll_area = pygame.Rect(
                self.category_left_button.right + gap,
                category_y,
                self.category_right_button.x - self.category_left_button.right - gap * 2,
                arrow_size,
            )
        else:
            self.category_left_button = None
            self.category_right_button = None
            self.category_scroll_area = pygame.Rect(self.left_panel.x + 14, category_y, self.left_panel.width - 28, arrow_size)

        self._draw_category_buttons()

        recipes = self._visible_recipes()
        self.recipe_rows = []
        row_y = category_y + 46
        row_height = 58
        for recipe in recipes:
            rect = pygame.Rect(self.left_panel.x + 14, row_y, self.left_panel.width - 28, row_height)
            selected = recipe.id == self.selected_recipe_id
            pygame.draw.rect(self.app.screen, COLORS["UI_PANEL"] if selected else COLORS["UI_SLOT"], rect, border_radius=10)
            pygame.draw.rect(
                self.app.screen,
                COLORS["UI_SLOT_SELECTED"] if selected else COLORS["UI_SLOT_BORDER"],
                rect,
                width=2,
                border_radius=10,
            )
            self._draw_recipe_list_row(recipe, rect)
            self.recipe_rows.append((recipe.id, rect))
            row_y += row_height + 10

        if not recipes:
            empty = self.text_font.render(self.localizer.t("ui.crafting.no_recipes"), True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(empty, (self.left_panel.x + 18, row_y))

    def _draw_category_buttons(self):
        categories = self._available_categories()
        total_width = 0
        for category in categories:
            label = self._category_label(category)
            total_width += max(74, self.small_font.size(label)[0] + 20) + 8
        self.category_content_width = max(0, total_width - 8)
        max_scroll = self._max_category_scroll()
        self.category_scroll_offset = max(0, min(self.category_scroll_offset, max_scroll))

        if self.category_left_button is not None:
            self._draw_category_arrow(self.category_left_button, "<", self.category_scroll_offset > 0)
        if self.category_right_button is not None:
            self._draw_category_arrow(self.category_right_button, ">", self.category_scroll_offset < max_scroll)

        button_x = self.category_scroll_area.x - self.category_scroll_offset
        previous_clip = self.app.screen.get_clip()
        self.app.screen.set_clip(self.category_scroll_area)
        for category in categories:
            label = self._category_label(category)
            width = max(74, self.small_font.size(label)[0] + 20)
            rect = pygame.Rect(button_x, self.category_scroll_area.y, width, self.category_scroll_area.height)
            active = category == self.active_category
            pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_SELECTED"] if active else COLORS["UI_SLOT"], rect, border_radius=8)
            pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], rect, width=1, border_radius=8)
            text = self.small_font.render(label, True, COLORS["WHITE"])
            self.app.screen.blit(text, text.get_rect(center=rect.center))
            self.category_buttons.append((category, rect.copy()))
            button_x = rect.right + 8
        self.app.screen.set_clip(previous_clip)

    def _draw_category_arrow(self, rect, label, enabled):
        fill = COLORS["UI_PANEL"] if enabled else COLORS["UI_SLOT"]
        pygame.draw.rect(self.app.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], rect, width=1, border_radius=8)
        color = COLORS["WHITE"] if enabled else COLORS["UI_TEXT_DIM"]
        text = self.text_font.render(label, True, color)
        self.app.screen.blit(text, text.get_rect(center=rect.center))

    def _draw_recipe_list_row(self, recipe, rect):
        unlocked = self.player.is_recipe_unlocked(recipe)
        can_unlock = self.player.can_unlock_recipe(recipe)
        can_craft = self.player.can_craft_recipe(recipe)
        result_definition = get_item_definition(recipe.result.item_id)
        icon = get_item_icon(result_definition, (34, 34))
        text_x = rect.x + 12
        if icon is not None:
            self.app.screen.blit(icon, (rect.x + 10, rect.y + 12))
            text_x = rect.x + 52

        title = recipe.localized_name() if unlocked or recipe.unlock_type != "knowledge" else self.localizer.t("ui.crafting.unknown_recipe")
        if recipe.is_temporary:
            title = f"[TEMP] {title}"
        title_text = self.text_font.render(title, True, COLORS["WHITE"])
        self.app.screen.blit(title_text, (text_x, rect.y + 8))

        if unlocked:
            status = self.localizer.t("ui.crafting.ready") if can_craft else self.localizer.t("ui.crafting.missing_materials")
            color = (150, 230, 150) if can_craft else COLORS["UI_TEXT_DIM"]
        else:
            status = self.localizer.t("ui.crafting.unlock_short", cost=recipe.knowledge_cost)
            color = (150, 230, 150) if can_unlock else (220, 150, 150)
        status_text = self.small_font.render(status, True, color)
        self.app.screen.blit(status_text, (text_x, rect.y + 32))

    def _draw_right_panel(self):
        pygame.draw.rect(self.app.screen, COLORS["UI_PANEL_ALT"], self.right_panel, border_radius=12)
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.right_panel, width=2, border_radius=12)

        shards = self.text_font.render(
            self.localizer.t("ui.crafting.knowledge_shards", count=self.player.knowledge_shards),
            True,
            COLORS["WHITE"],
        )
        self.app.screen.blit(shards, (self.right_panel.x + 16, self.right_panel.y + 14))

        recipe = self._selected_recipe()
        if recipe is None:
            return

        result_stack = create_item_stack(recipe.result.item_id, recipe.result.quantity)
        result_name = result_stack.name if result_stack is not None else recipe.result.item_id
        result_definition = get_item_definition(recipe.result.item_id)

        recipe_title = recipe.localized_name()
        if recipe.is_temporary:
            recipe_title = f"[TEMP] {recipe_title}"
        title = self.section_font.render(recipe_title, True, COLORS["WHITE"])
        self.app.screen.blit(title, (self.right_panel.x + 16, self.right_panel.y + 54))

        desc_lines = _wrap_text(recipe.localized_description(), self.text_font, self.right_panel.width - 32)
        for index, line in enumerate(desc_lines[:3]):
            text = self.text_font.render(line, True, COLORS["UI_TEXT_DIM"])
            self.app.screen.blit(text, (self.right_panel.x + 16, self.right_panel.y + 88 + index * 24))

        result_y = self.right_panel.y + 168
        result_icon = get_item_icon(result_definition, (36, 36))
        if result_icon is not None:
            self.app.screen.blit(result_icon, (self.right_panel.x + 16, result_y))
            result_text_x = self.right_panel.x + 60
        else:
            result_text_x = self.right_panel.x + 16
        result_text = self.text_font.render(
            self.localizer.t("ui.crafting.result", name=result_name, quantity=recipe.result.quantity),
            True,
            COLORS["WHITE"],
        )
        self.app.screen.blit(result_text, (result_text_x, result_y + 6))

        material_title = self.text_font.render(self.localizer.t("ui.crafting.materials"), True, COLORS["WHITE"])
        self.app.screen.blit(material_title, (self.right_panel.x + 16, self.right_panel.y + 214))
        row_y = self.right_panel.y + 246
        for ingredient in recipe.ingredients:
            item_definition = get_item_definition(ingredient.item_id)
            label = item_definition.localized_name() if item_definition is not None else ingredient.item_id
            current = self.player.inventory.count_item(ingredient.item_id) + self.player.quest_inventory.count_item(ingredient.item_id)
            enough = current >= ingredient.quantity
            color = (150, 230, 150) if enough else (220, 150, 150)
            icon = get_item_icon(item_definition, (24, 24))
            if icon is not None:
                self.app.screen.blit(icon, (self.right_panel.x + 16, row_y - 2))
                line_x = self.right_panel.x + 48
            else:
                line_x = self.right_panel.x + 16
            line = self.text_font.render(f"{label}: {current}/{ingredient.quantity}", True, color)
            self.app.screen.blit(line, (line_x, row_y))
            row_y += 26

        status_y = max(row_y + 12, self.right_panel.bottom - 120)
        if not self.player.is_recipe_unlocked(recipe) and recipe.unlock_type == "knowledge":
            unlock_text = self.text_font.render(
                self.localizer.t("ui.crafting.unlock_cost", cost=recipe.knowledge_cost),
                True,
                COLORS["WHITE"],
            )
            self.app.screen.blit(unlock_text, (self.right_panel.x + 16, status_y))
            status_y += 30

        status = self._recipe_status_text(recipe)
        status_text = self.small_font.render(status, True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(status_text, (self.right_panel.x + 16, status_y))

        self.action_button = pygame.Rect(self.right_panel.x + 16, self.right_panel.bottom - 58, 180, 40)
        action_label, action_enabled = self._primary_action(recipe)
        pygame.draw.rect(
            self.app.screen,
            COLORS["UI_SLOT_SELECTED"] if action_enabled else COLORS["UI_SLOT"],
            self.action_button,
            border_radius=10,
        )
        pygame.draw.rect(self.app.screen, COLORS["UI_SLOT_BORDER"], self.action_button, width=2, border_radius=10)
        label = self.text_font.render(action_label, True, COLORS["WHITE"])
        self.app.screen.blit(label, label.get_rect(center=self.action_button.center))

    def _available_categories(self):
        categories = ["all"]
        for recipe in get_recipe_definitions():
            if recipe.required_flags and not self.player.has_flags(recipe.required_flags):
                continue
            if recipe.category not in categories:
                categories.append(recipe.category)
        return categories

    def _visible_recipes(self):
        visible = []
        for recipe in get_recipe_definitions():
            if recipe.required_flags and not self.player.has_flags(recipe.required_flags):
                continue
            if self.active_category != "all" and recipe.category != self.active_category:
                continue
            visible.append(recipe)
        return visible

    def _selected_recipe(self):
        for recipe in self._visible_recipes():
            if recipe.id == self.selected_recipe_id:
                return recipe
        return None

    def _ensure_selected_recipe(self):
        recipes = self._visible_recipes()
        if not recipes:
            self.selected_recipe_id = None
            return
        if self.selected_recipe_id not in {recipe.id for recipe in recipes}:
            self.selected_recipe_id = recipes[0].id
        self._ensure_active_category_visible()

    def _move_selection(self, direction):
        recipes = self._visible_recipes()
        if not recipes:
            return
        ids = [recipe.id for recipe in recipes]
        if self.selected_recipe_id not in ids:
            self.selected_recipe_id = ids[0]
            return
        index = ids.index(self.selected_recipe_id)
        self.selected_recipe_id = ids[(index + direction) % len(ids)]

    def _switch_category(self, direction):
        categories = self._available_categories()
        if self.active_category not in categories:
            self.active_category = categories[0]
            self._ensure_selected_recipe()
            return
        index = categories.index(self.active_category)
        self.active_category = categories[(index + direction) % len(categories)]
        self._ensure_selected_recipe()
        self._ensure_active_category_visible()

    def _handle_click(self, mouse_pos):
        if self.category_left_button is not None and self.category_left_button.collidepoint(mouse_pos):
            self._scroll_categories(-120)
            return
        if self.category_right_button is not None and self.category_right_button.collidepoint(mouse_pos):
            self._scroll_categories(120)
            return

        for category, rect in self.category_buttons:
            if rect.collidepoint(mouse_pos):
                self.active_category = category
                self._ensure_selected_recipe()
                self._ensure_active_category_visible()
                return
        for recipe_id, rect in self.recipe_rows:
            if rect.collidepoint(mouse_pos):
                self.selected_recipe_id = recipe_id
                return
        if self.action_button is not None and self.action_button.collidepoint(mouse_pos):
            self._perform_primary_action()

    def _primary_action(self, recipe):
        if recipe is None:
            return self.localizer.t("ui.crafting.action_unavailable"), False
        if not self.player.is_recipe_unlocked(recipe) and recipe.unlock_type == "knowledge":
            return self.localizer.t("ui.crafting.action_unlock"), self.player.can_unlock_recipe(recipe)
        return self.localizer.t("ui.crafting.action_craft"), self.player.can_craft_recipe(recipe)

    def _recipe_status_text(self, recipe):
        if recipe is None:
            return ""
        if not self.player.is_recipe_unlocked(recipe):
            if recipe.unlock_type == "knowledge":
                if self.player.can_unlock_recipe(recipe):
                    return self.localizer.t("ui.crafting.status_can_unlock")
                return self.localizer.t("ui.crafting.status_need_more_shards")
            return self.localizer.t("ui.crafting.status_locked")
        if self.player.can_craft_recipe(recipe):
            return self.localizer.t("ui.crafting.status_ready")
        if not self.player.can_add_item(recipe.result.item_id, recipe.result.quantity):
            return self.localizer.t("ui.crafting.status_no_space")
        return self.localizer.t("ui.crafting.status_missing")

    def _perform_primary_action(self):
        recipe = self._selected_recipe()
        if recipe is None:
            return

        if not self.player.is_recipe_unlocked(recipe) and recipe.unlock_type == "knowledge":
            if not self.player.can_unlock_recipe(recipe):
                self._set_message(self.localizer.t("ui.crafting.message_not_enough_shards"))
                return
            if not self.player.spend_knowledge_shards(recipe.knowledge_cost):
                self._set_message(self.localizer.t("ui.crafting.message_not_enough_shards"))
                return
            self.player.unlock_recipe(recipe.id)
            self._set_message(self.localizer.t("ui.crafting.message_unlocked", name=recipe.localized_name()))
            return

        if not self.player.can_craft_recipe(recipe):
            if not self.player.can_add_item(recipe.result.item_id, recipe.result.quantity):
                self._set_message(self.localizer.t("ui.crafting.message_inventory_full"))
            else:
                self._set_message(self.localizer.t("ui.crafting.message_missing_materials"))
            return

        if not self.player.craft_recipe(recipe):
            self._set_message(self.localizer.t("ui.crafting.message_crafting_failed"))
            return

        result_stack = create_item_stack(recipe.result.item_id, recipe.result.quantity)
        result_name = result_stack.name if result_stack is not None else recipe.result.item_id
        self._set_message(self.localizer.t("ui.crafting.message_crafted", name=result_name, quantity=recipe.result.quantity))

    def _set_message(self, text):
        self.message = text
        self.message_timer = 2.0

    def _category_scroll_needed(self):
        categories = self._available_categories()
        total_width = 0
        for category in categories:
            label = self._category_label(category)
            total_width += max(74, self.small_font.size(label)[0] + 20) + 8
        visible_width = self.left_panel.width - 28
        return total_width - 8 > visible_width

    def _max_category_scroll(self):
        if self.category_scroll_area is None:
            return 0
        return max(0, self.category_content_width - self.category_scroll_area.width)

    def _scroll_categories(self, delta):
        self.category_scroll_offset = max(0, min(self.category_scroll_offset + delta, self._max_category_scroll()))

    def _ensure_active_category_visible(self):
        if self.category_scroll_area is None:
            return
        categories = self._available_categories()
        button_x = self.category_scroll_area.x
        for category in categories:
            label = self._category_label(category)
            width = max(74, self.small_font.size(label)[0] + 20)
            if category == self.active_category:
                left = button_x - self.category_scroll_offset
                right = left + width
                if left < self.category_scroll_area.x:
                    self.category_scroll_offset = max(0, button_x - self.category_scroll_area.x)
                elif right > self.category_scroll_area.right:
                    self.category_scroll_offset = min(self._max_category_scroll(), button_x + width - self.category_scroll_area.right)
                return
            button_x += width + 8

    def _category_label(self, category):
        key = f"ui.crafting.category_{category}"
        translated = self.localizer.t(key)
        return translated if translated != key else category.title()


def _wrap_text(text, font, max_width):
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
