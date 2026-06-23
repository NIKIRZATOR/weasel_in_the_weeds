import pygame

from game.core.assets import load_image
from game.effects import get_effect_definition
from game.items import get_item_icon
from game.localization import get_localizer
from settings import ASSETS_DIR, COLORS, HOTBAR_SIZE, PLAYER_MAX_HEALTH, PLAYER_MAX_STAMINA


class HUD:
    def __init__(self):
        self.localizer = get_localizer()
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 22)
        self.tiny_font = pygame.font.Font(None, 18)
        self.portrait_radius = 32
        self.effect_rects = []
        self.effect_icon_cache = {}

    def on_language_changed(self):
        return None

    def draw_portrait(self, screen, player):
        radius = self.portrait_radius
        x = 16 + radius
        y = 16 + radius
        portrait_rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

        pygame.draw.circle(screen, COLORS["UI_PANEL"], (x, y), radius + 4)
        pygame.draw.circle(screen, COLORS["UI_SLOT_BORDER"], (x, y), radius + 4, width=2)

        portrait = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        clip_circle = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(clip_circle, (255, 255, 255, 255), (radius, radius), radius)

        if player.sprite is not None:
            head_crop_height = max(1, int(player.sprite.get_height() * 0.56))
            crop_rect = pygame.Rect(0, 0, player.sprite.get_width(), head_crop_height)
            head = pygame.Surface((crop_rect.width, crop_rect.height), pygame.SRCALPHA)
            head.blit(player.sprite, (0, 0), crop_rect)
            scale_width = int(radius * 1.4)
            scale_height = int(radius * 1.4)
            head = pygame.transform.smoothscale(head, (scale_width, scale_height))
            head_rect = head.get_rect(center=(radius, radius + 6))
            portrait.blit(head, head_rect)
        else:
            pygame.draw.circle(portrait, COLORS["PLAYER"], (radius, radius + 4), int(radius * 0.72))

        portrait.blit(clip_circle, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(portrait, portrait_rect.topleft)

    def draw_health_bar(self, screen, player):
        width = 188
        height = 16
        x = 96
        y = 18

        max_health = max(1, int(player.get_max_health()))
        current_health = max(0, int(player.health))
        percent = current_health / max_health

        pygame.draw.rect(screen, COLORS['HEALTH_BG'], (x, y, width, height), border_radius=6)
        pygame.draw.rect(screen, COLORS['HEALTH'], (x, y, width * percent, height), border_radius=6)

        text = self.font.render(
            f"{self.localizer.t('ui.inventory.stat_hp')}: {current_health}/{max_health}",
            True,
            COLORS['WHITE'],
        )
        screen.blit(text, (x + width + 8, y - 4))

    def draw_stamina_bar(self, screen, player):
        width = 188
        height = 13
        x = 96
        y = 40

        max_stamina = max(1, int(player.get_max_stamina()))
        current_stamina = max(0, int(player.stamina))
        percent = current_stamina / max_stamina

        pygame.draw.rect(screen, COLORS['STAMINA_BG'], (x, y, width, height), border_radius=6)
        pygame.draw.rect(screen, COLORS['STAMINA'], (x, y, width * percent, height), border_radius=6)

        text = self.font.render(
            f"{self.localizer.t('ui.inventory.stat_st')}: {current_stamina}/{max_stamina}",
            True,
            COLORS['WHITE'],
        )
        screen.blit(text, (x + width + 8, y - 4))

    def draw_progression_bar(self, screen, player):
        width = 188
        height = 10
        x = 96
        y = 58
        required_xp = max(1, int(player.get_xp_to_next_level()))
        current_xp = max(0, int(player.xp))
        percent = current_xp / required_xp

        pygame.draw.rect(screen, COLORS["UI_PANEL"], (x, y, width, height), border_radius=5)
        pygame.draw.rect(screen, COLORS["UI_SLOT_SELECTED"], (x, y, width * percent, height), border_radius=5)
        pygame.draw.rect(screen, COLORS["UI_SLOT_BORDER"], (x, y, width, height), width=1, border_radius=5)

        level_text = self.tiny_font.render(f"Lv. {player.level}", True, COLORS["WHITE"])
        xp_text = self.tiny_font.render(f"XP {current_xp}/{required_xp}", True, COLORS["WHITE"])
        info_y = y + height + 4

        level_rect = pygame.Rect(x, info_y - 1, level_text.get_width() + 10, level_text.get_height() + 4)
        xp_rect = pygame.Rect(level_rect.right + 8, info_y - 1, xp_text.get_width() + 10, xp_text.get_height() + 4)

        pygame.draw.rect(screen, COLORS["UI_PANEL"], level_rect, border_radius=5)
        pygame.draw.rect(screen, COLORS["UI_PANEL"], xp_rect, border_radius=5)
        pygame.draw.rect(screen, COLORS["UI_SLOT_BORDER"], level_rect, width=1, border_radius=5)
        pygame.draw.rect(screen, COLORS["UI_SLOT_BORDER"], xp_rect, width=1, border_radius=5)

        screen.blit(level_text, (level_rect.x + 5, level_rect.y + 2))
        screen.blit(xp_text, (xp_rect.x + 5, xp_rect.y + 2))

    def draw_active_effects(self, screen, player):
        self.effect_rects = []
        if not player.active_effects:
            return

        slot_width = 88
        slot_height = 26
        gap = 6
        x = 16
        y = 16 + self.portrait_radius * 2 + 18
        mouse_pos = pygame.mouse.get_pos()
        hovered_effect = None

        for effect in player.active_effects:
            definition = get_effect_definition(effect.effect_type)
            is_positive = True if definition is None else definition.is_positive
            fill = (54, 88, 64) if is_positive else (92, 62, 62)
            border = (140, 230, 170) if is_positive else (230, 150, 150)
            rect = pygame.Rect(x, y, slot_width, slot_height)

            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, width=2, border_radius=8)

            icon = self._get_effect_icon(effect, (18, 18))
            if icon is not None:
                screen.blit(icon, (rect.x + 6, rect.y + (rect.height - icon.get_height()) // 2))
                label_x = rect.x + 30
            else:
                label = self._effect_short_label(effect.effect_type)
                label_text = self.tiny_font.render(label, True, COLORS["WHITE"])
                screen.blit(label_text, (rect.x + 8, rect.y + 5))
                label_x = rect.x + 30

            time_text = self.tiny_font.render(f"{max(0.0, effect.remaining):.1f}s", True, COLORS["WHITE"])
            screen.blit(time_text, (rect.right - time_text.get_width() - 6, rect.y + 5))
            if icon is not None:
                short_name = self._effect_short_label(effect.effect_type)
                label_text = self.tiny_font.render(short_name, True, COLORS["WHITE"])
                screen.blit(label_text, (label_x, rect.y + 5))

            self.effect_rects.append((rect, effect))
            if rect.collidepoint(mouse_pos):
                hovered_effect = effect

            y += slot_height + gap

        if hovered_effect is not None:
            self._draw_effect_tooltip(screen, hovered_effect, mouse_pos)

    def _effect_short_label(self, effect_type):
        name = self._effect_name(effect_type)
        words = str(name).split()
        if not words:
            return "FX"
        if len(words) == 1:
            return words[0][:3].upper()
        return "".join(word[:1] for word in words[:3]).upper()

    def _effect_key(self, effect_type):
        return effect_type.value if hasattr(effect_type, "value") else str(effect_type)

    def _get_effect_icon(self, effect, size):
        definition = get_effect_definition(effect.effect_type)
        if definition is None or not definition.icon_path:
            return None

        cache_key = (definition.icon_path, size)
        if cache_key in self.effect_icon_cache:
            return self.effect_icon_cache[cache_key]

        icon = load_image(ASSETS_DIR / definition.icon_path, size=size)
        self.effect_icon_cache[cache_key] = icon
        return icon

    def _effect_name(self, effect_type):
        effect_key = self._effect_key(effect_type)
        key = f"ui.effects.{effect_key}.name"
        translated = self.localizer.t(key)
        if translated != key:
            return translated
        return effect_key.replace("_", " ").title()

    def _effect_description(self, effect):
        effect_key = self._effect_key(effect.effect_type)
        key = f"ui.effects.{effect_key}.description"
        translated = self.localizer.t(key)
        if translated != key:
            return translated
        definition = get_effect_definition(effect.effect_type)
        return definition.description if definition is not None else str(effect.effect_type)

    def _effect_value_text(self, effect):
        value = effect.value
        effect_type = self._effect_key(effect.effect_type)
        if effect_type in {"slowed", "damage_increased", "damage_reduced", "fatigue"}:
            return f"{int(round(value * 100))}%"
        return str(int(round(value))) if abs(value - round(value)) < 0.05 else f"{value:.1f}"

    def _draw_effect_tooltip(self, screen, effect, mouse_pos):
        name = self._effect_name(effect.effect_type)
        description = self._effect_description(effect)
        stats = self.localizer.t(
            "ui.effects.tooltip_stats",
            value=self._effect_value_text(effect),
            duration=f"{max(0.0, effect.remaining):.1f}",
        )

        lines = [name, description, stats]
        rendered_lines = [
            self.small_font.render(lines[0], True, COLORS["WHITE"]),
            self.tiny_font.render(lines[1], True, COLORS["WHITE"]),
            self.tiny_font.render(lines[2], True, COLORS["UI_TEXT_DIM"]),
        ]
        width = max(surface.get_width() for surface in rendered_lines) + 16
        height = sum(surface.get_height() for surface in rendered_lines) + 16
        tooltip_rect = pygame.Rect(mouse_pos[0] + 14, mouse_pos[1] + 14, width, height)

        screen_width, screen_height = screen.get_size()
        if tooltip_rect.right > screen_width - 8:
            tooltip_rect.x = mouse_pos[0] - width - 14
        if tooltip_rect.bottom > screen_height - 8:
            tooltip_rect.y = mouse_pos[1] - height - 14

        pygame.draw.rect(screen, COLORS["UI_PANEL"], tooltip_rect, border_radius=8)
        pygame.draw.rect(screen, COLORS["UI_SLOT_BORDER"], tooltip_rect, width=2, border_radius=8)

        draw_y = tooltip_rect.y + 8
        for index, surface in enumerate(rendered_lines):
            screen.blit(surface, (tooltip_rect.x + 8, draw_y))
            draw_y += surface.get_height() + (4 if index == 0 else 2)

    def draw_coins(self, screen, player):
        screen_width, _ = screen.get_size()
        text = self.font.render(
            f"{self.localizer.t('ui.inventory.stat_coins')}: {player.coins}",
            True,
            COLORS['GOLD'],
        )
        screen.blit(text, (screen_width - text.get_width() - 16, 72))

    def draw_knowledge_shards(self, screen, player):
        screen_width, _ = screen.get_size()
        text = self.small_font.render(
            f"{self.localizer.t('ui.inventory.stat_shards')}: {player.knowledge_shards}",
            True,
            COLORS['WHITE'],
        )
        screen.blit(text, (screen_width - text.get_width() - 16, 102))

    def draw_fps(self, screen, fps):
        screen_width, _ = screen.get_size()
        text = self.small_font.render(f"FPS: {int(round(max(0.0, float(fps))))}", True, COLORS["WHITE"])
        screen.blit(text, (screen_width - text.get_width() - 16, 130))

    def draw_hotbar(self, screen, player, combat_state=None):
        screen_width, screen_height = screen.get_size()
        slot_size = 54
        gap = 8
        weapon_slot_gap = 14
        total_width = (HOTBAR_SIZE + 1) * slot_size + (HOTBAR_SIZE - 1) * gap + weapon_slot_gap
        start_x = (screen_width - total_width) // 2
        y = screen_height - slot_size - 12

        weapon_rect = pygame.Rect(start_x, y, slot_size, slot_size)
        self._draw_weapon_slot(screen, player, weapon_rect, combat_state=combat_state)
        hotbar_start_x = weapon_rect.right + weapon_slot_gap

        for index in range(HOTBAR_SIZE):
            rect = pygame.Rect(hotbar_start_x + index * (slot_size + gap), y, slot_size, slot_size)
            selected = index == player.selected_hotbar_index
            stack = player.get_hotbar_stack(index)

            fill = COLORS['UI_PANEL_ALT'] if selected else COLORS['UI_PANEL']
            border = COLORS['UI_SLOT_SELECTED'] if selected else COLORS['UI_SLOT_BORDER']
            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, width=2, border_radius=8)

            key_text = self.tiny_font.render(str(index + 1), True, COLORS['UI_TEXT_DIM'])
            screen.blit(key_text, (rect.x + 4, rect.y + 2))

            if stack is not None:
                icon = get_item_icon(stack.definition, (slot_size - 16, slot_size - 16))
                if icon is not None:
                    screen.blit(icon, icon.get_rect(center=rect.center))
                else:
                    label = stack.name[:2].upper()
                    item_text = self.small_font.render(label, True, COLORS['WHITE'])
                    screen.blit(item_text, item_text.get_rect(center=rect.center))

                if stack.quantity > 1:
                    qty_text = self.tiny_font.render(str(stack.quantity), True, COLORS['WHITE'])
                    screen.blit(qty_text, (rect.right - qty_text.get_width() - 4, rect.bottom - qty_text.get_height() - 2))

    def _draw_weapon_slot(self, screen, player, rect, combat_state=None):
        stack = player.get_equipped_weapon()
        pygame.draw.rect(screen, COLORS['UI_PANEL_ALT'], rect, border_radius=8)
        pygame.draw.rect(screen, COLORS['UI_SLOT_SELECTED'], rect, width=2, border_radius=8)

        label = self.tiny_font.render("W", True, COLORS['UI_TEXT_DIM'])
        screen.blit(label, (rect.x + 4, rect.y + 2))

        if stack is None:
            return

        icon = get_item_icon(stack.definition, (rect.width - 16, rect.height - 16))
        if icon is not None:
            screen.blit(icon, icon.get_rect(center=rect.center))
        else:
            item_text = self.small_font.render(stack.name[:2].upper(), True, COLORS['WHITE'])
            screen.blit(item_text, item_text.get_rect(center=rect.center))

    def draw_controls(self, screen):
        _, screen_height = screen.get_size()
        controls_text = self.localizer.t("ui.hud.controls")
        text = self.small_font.render(controls_text, True, (200, 200, 200))
        screen.blit(text, (10, screen_height - 32))

    def draw_map_hint(self, screen, player):
        if not player.can_open_map():
            return

        screen_width, _ = screen.get_size()
        text = self.small_font.render(self.localizer.t("ui.hud.map_hint"), True, COLORS["WHITE"])
        screen.blit(text, (screen_width - text.get_width() - 16, 66))

    def draw_active_quest(self, screen, quest_manager):
        if quest_manager is None:
            return

        quest = quest_manager.get_active_main_quest()
        if quest is None:
            return

        screen_width, _ = screen.get_size()
        panel_width = min(320, screen_width - 24)
        panel_height = 54
        panel_rect = pygame.Rect(screen_width - panel_width - 16, 10, panel_width, panel_height)
        pygame.draw.rect(screen, COLORS["UI_PANEL"], panel_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["UI_SLOT_BORDER"], panel_rect, width=2, border_radius=10)

        title = self.tiny_font.render(self.localizer.t("ui.quests.active_label"), True, COLORS["UI_TEXT_DIM"])
        text = self.small_font.render(self.localizer.t(quest.title_key), True, COLORS["WHITE"])
        screen.blit(title, (panel_rect.x + 10, panel_rect.y + 7))
        screen.blit(text, (panel_rect.x + 10, panel_rect.y + 24))

    def draw_combat_status(self, screen, combat_state):
        if combat_state is None:
            return

        screen_width, screen_height = screen.get_size()
        weapon_name = str(combat_state.get("weapon_name", "") or "")
        if weapon_name:
            weapon_text = self.small_font.render(weapon_name, True, COLORS["WHITE"])
            screen.blit(
                weapon_text,
                weapon_text.get_rect(center=(screen_width // 2, screen_height - 82)),
            )

        if combat_state.get("charging"):
            bar_width = min(240, screen_width - 80)
            bar_height = 12
            bar_x = (screen_width - bar_width) // 2
            bar_y = screen_height - 62
            progress = max(0.0, min(1.0, float(combat_state.get("charge_progress", 0.0))))
            pygame.draw.rect(screen, COLORS["UI_PANEL"], (bar_x, bar_y, bar_width, bar_height), border_radius=6)
            pygame.draw.rect(
                screen,
                COLORS["UI_SLOT_SELECTED"],
                (bar_x, bar_y, bar_width * progress, bar_height),
                border_radius=6,
            )
            pygame.draw.rect(screen, COLORS["UI_SLOT_BORDER"], (bar_x, bar_y, bar_width, bar_height), width=2, border_radius=6)

        if combat_state.get("not_enough_stamina"):
            warning = self.small_font.render(self.localizer.t("ui.combat.no_stamina"), True, (255, 180, 130))
            screen.blit(
                warning,
                warning.get_rect(center=(screen_width // 2, screen_height - 104)),
            )

    def draw(self, screen, player, quest_manager=None, combat_state=None, fps=0.0, show_fps=True):
        self.draw_portrait(screen, player)
        self.draw_active_effects(screen, player)
        self.draw_health_bar(screen, player)
        self.draw_stamina_bar(screen, player)
        self.draw_progression_bar(screen, player)
        self.draw_active_quest(screen, quest_manager)
        self.draw_coins(screen, player)
        self.draw_knowledge_shards(screen, player)
        if show_fps:
            self.draw_fps(screen, fps)
        self.draw_map_hint(screen, player)
        self.draw_hotbar(screen, player, combat_state=combat_state)
        self.draw_combat_status(screen, combat_state)
        self.draw_controls(screen)
