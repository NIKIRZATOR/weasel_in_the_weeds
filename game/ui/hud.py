import pygame
from settings import COLORS, PLAYER_MAX_HEALTH, PLAYER_MAX_STAMINA, SCREEN_HEIGHT

class HUD:
    """Интерфейс игрока"""
    
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
    
    def draw_health_bar(self, screen, current_health):
        width = 200
        height = 20
        x, y = 10, 10
        
        percent = current_health / PLAYER_MAX_HEALTH
        
        pygame.draw.rect(screen, COLORS['HEALTH_BG'], (x, y, width, height))
        pygame.draw.rect(screen, COLORS['HEALTH'], (x, y, width * percent, height))
        
        text = self.font.render(f"HP: {int(current_health)}", True, COLORS['WHITE'])
        screen.blit(text, (x + width + 10, y - 2))
    
    def draw_stamina_bar(self, screen, current_stamina):
        width = 200
        height = 15
        x, y = 10, 35
        
        percent = current_stamina / PLAYER_MAX_STAMINA
        
        pygame.draw.rect(screen, COLORS['STAMINA_BG'], (x, y, width, height))
        pygame.draw.rect(screen, COLORS['STAMINA'], (x, y, width * percent, height))
        
        text = self.font.render(f"ST: {int(current_stamina)}", True, COLORS['WHITE'])
        screen.blit(text, (x + width + 10, y - 2))
    
    def draw_controls(self, screen):
        controls_text = "WASD - move | SHIFT - run | SPACE - jump | F - attack"
        text = self.small_font.render(controls_text, True, (200, 200, 200))
        screen.blit(text, (10, SCREEN_HEIGHT - 30))
    
    def draw(self, screen, player):
        self.draw_health_bar(screen, player.health)
        self.draw_stamina_bar(screen, player.stamina)
        self.draw_controls(screen)