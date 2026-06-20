import pygame

from game.items import get_item_icon
from game.localization import get_localizer
from settings import COLORS, HOTBAR_SIZE, PLAYER_MAX_HEALTH, PLAYER_MAX_STAMINA


class HUD:
    

    def __init__(self):
        self.localizer = get_localizer()
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 22)
        self.tiny_font = pygame.font.Font(None, 18)
        self.portrait_radius = 32

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

    def draw_coins(self, screen, player):
        screen_width, _ = screen.get_size()
        text = self.font.render(
            f"{self.localizer.t('ui.inventory.stat_coins')}: {player.coins}",
            True,
            COLORS['GOLD'],
        )
        screen.blit(text, (screen_width - text.get_width() - 16, 10))

    def draw_knowledge_shards(self, screen, player):
        screen_width, _ = screen.get_size()
        text = self.small_font.render(
            f"{self.localizer.t('ui.inventory.stat_shards')}: {player.knowledge_shards}",
            True,
            COLORS['WHITE'],
        )
        screen.blit(text, (screen_width - text.get_width() - 16, 42))

    def draw_hotbar(self, screen, player):
        screen_width, screen_height = screen.get_size()
        slot_size = 54
        gap = 8
        weapon_slot_gap = 14
        total_width = (HOTBAR_SIZE + 1) * slot_size + (HOTBAR_SIZE - 1) * gap + weapon_slot_gap
        start_x = (screen_width - total_width) // 2
        y = screen_height - slot_size - 12

        weapon_rect = pygame.Rect(start_x, y, slot_size, slot_size)
        self._draw_weapon_slot(screen, player, weapon_rect)
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

    def _draw_weapon_slot(self, screen, player, rect):
        stack = player.get_equipped_weapon()
        pygame.draw.rect(screen, COLORS['UI_PANEL_ALT'], rect, border_radius=8)
        pygame.draw.rect(screen, COLORS['UI_SLOT_SELECTED'], rect, width=2, border_radius=8)

        label = self.tiny_font.render("Weapon", True, COLORS['UI_TEXT_DIM'])
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

    def draw(self, screen, player):
        self.draw_portrait(screen, player)
        self.draw_health_bar(screen, player)
        self.draw_stamina_bar(screen, player)
        self.draw_coins(screen, player)
        self.draw_knowledge_shards(screen, player)
        self.draw_map_hint(screen, player)
        self.draw_hotbar(screen, player)
        self.draw_controls(screen)
