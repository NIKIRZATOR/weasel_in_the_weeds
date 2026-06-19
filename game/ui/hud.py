import pygame

from settings import COLORS, HOTBAR_SIZE, PLAYER_MAX_HEALTH, PLAYER_MAX_STAMINA


class HUD:
    """Интерфейс игрока"""
    

    def __init__(self):
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 22)
        self.tiny_font = pygame.font.Font(None, 18)

    def draw_health_bar(self, screen, player):
        width = 220
        height = 20
        x, y = 10, 10

        max_health = max(1, int(player.get_max_health()))
        current_health = max(0, int(player.health))
        percent = current_health / max_health

        pygame.draw.rect(screen, COLORS['HEALTH_BG'], (x, y, width, height), border_radius=6)
        pygame.draw.rect(screen, COLORS['HEALTH'], (x, y, width * percent, height), border_radius=6)

        text = self.font.render(f"HP: {current_health}/{max_health}", True, COLORS['WHITE'])
        screen.blit(text, (x + width + 10, y - 2))

    def draw_stamina_bar(self, screen, player):
        width = 220
        height = 15
        x, y = 10, 36

        max_stamina = max(1, int(player.get_max_stamina()))
        current_stamina = max(0, int(player.stamina))
        percent = current_stamina / max_stamina

        pygame.draw.rect(screen, COLORS['STAMINA_BG'], (x, y, width, height), border_radius=6)
        pygame.draw.rect(screen, COLORS['STAMINA'], (x, y, width * percent, height), border_radius=6)

        text = self.font.render(f"ST: {current_stamina}/{max_stamina}", True, COLORS['WHITE'])
        screen.blit(text, (x + width + 10, y - 2))

    def draw_coins(self, screen, player):
        screen_width, _ = screen.get_size()
        text = self.font.render(f"Coins: {player.coins}", True, COLORS['GOLD'])
        screen.blit(text, (screen_width - text.get_width() - 16, 10))

    def draw_hotbar(self, screen, player):
        screen_width, screen_height = screen.get_size()
        slot_size = 54
        gap = 8
        total_width = HOTBAR_SIZE * slot_size + (HOTBAR_SIZE - 1) * gap
        start_x = (screen_width - total_width) // 2
        y = screen_height - slot_size - 12

        for index in range(HOTBAR_SIZE):
            rect = pygame.Rect(start_x + index * (slot_size + gap), y, slot_size, slot_size)
            selected = index == player.selected_hotbar_index
            stack = player.get_hotbar_stack(index)

            fill = COLORS['UI_PANEL_ALT'] if selected else COLORS['UI_PANEL']
            border = COLORS['UI_SLOT_SELECTED'] if selected else COLORS['UI_SLOT_BORDER']
            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, width=2, border_radius=8)

            key_text = self.tiny_font.render(str(index + 1), True, COLORS['UI_TEXT_DIM'])
            screen.blit(key_text, (rect.x + 4, rect.y + 2))

            if stack is not None:
                label = stack.name[:2].upper()
                item_text = self.small_font.render(label, True, COLORS['WHITE'])
                screen.blit(item_text, item_text.get_rect(center=rect.center))

                if stack.quantity > 1:
                    qty_text = self.tiny_font.render(str(stack.quantity), True, COLORS['WHITE'])
                    screen.blit(qty_text, (rect.right - qty_text.get_width() - 4, rect.bottom - qty_text.get_height() - 2))

    def draw_controls(self, screen):
        _, screen_height = screen.get_size()
        controls_text = "WASD - move | SHIFT - run | SPACE - jump | ALT - dash | LMB - attack | E - interact | I - inventory"
        text = self.small_font.render(controls_text, True, (200, 200, 200))
        screen.blit(text, (10, screen_height - 32))

    def draw(self, screen, player):
        self.draw_health_bar(screen, player)
        self.draw_stamina_bar(screen, player)
        self.draw_coins(screen, player)
        self.draw_hotbar(screen, player)
        self.draw_controls(screen)
