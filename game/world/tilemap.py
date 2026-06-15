import pygame
from settings import COLORS, TILE_SIZE

class TileMap:
    """Управление тайловой картой"""
    
    TILE_TYPES = {
        0: 'grass',
        1: 'wall',
        2: 'water',
        3: 'path'
    }
    
    def __init__(self, ground_layer, obstacle_layer):
        self.ground_layer = ground_layer
        self.obstacle_layer = obstacle_layer
        self.width = len(ground_layer[0])
        self.height = len(ground_layer)
        self.tile_size = TILE_SIZE
    
    def get_tile_type(self, x, y):
        """Возвращает тип тайла на позиции"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.ground_layer[y][x]
        return 1  # Стена для границ
    
    def get_obstacle(self, x, y):
        """Возвращает препятствие на позиции"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.obstacle_layer[y][x]
        return 0
    
    def get_tile_color(self, tile_type):
        """Возвращает цвет для типа тайла"""
        color_map = {
            0: COLORS['GRASS'],
            1: COLORS['WALL'],
            2: COLORS['WATER'],
            3: COLORS['PATH']
        }
        return color_map.get(tile_type, (255, 0, 255))
    
    def is_walkable(self, x, y, ignore_obstacles=False):
        """Проверяет, можно ли ходить по тайлу"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        
        # Стены
        if self.ground_layer[y][x] == 1:
            return False
        
        # Препятствия
        if not ignore_obstacles:
            obstacle = self.obstacle_layer[y][x]
            if obstacle == 1 or obstacle == 2:
                return False
        
        return True
    
    def draw(self, screen, camera):
        """Рисует карту с учетом камеры"""
        # Используем camera.position.x и camera.position.y вместо camera.x и camera.y
        start_x = max(0, int(camera.position.x // self.tile_size))
        end_x = min(self.width, int((camera.position.x + screen.get_width()) // self.tile_size + 1))
        start_y = max(0, int(camera.position.y // self.tile_size))
        end_y = min(self.height, int((camera.position.y + screen.get_height()) // self.tile_size + 1))
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = x * self.tile_size - camera.position.x
                screen_y = y * self.tile_size - camera.position.y
                
                # Рисуем землю
                tile_type = self.ground_layer[y][x]
                color = self.get_tile_color(tile_type)
                pygame.draw.rect(screen, color, 
                               (screen_x, screen_y, self.tile_size, self.tile_size))
                pygame.draw.rect(screen, COLORS['BLACK'], 
                               (screen_x, screen_y, self.tile_size, self.tile_size), 1)
                
                # Рисуем препятствия
                obstacle = self.obstacle_layer[y][x]
                if obstacle == 1:
                    pygame.draw.ellipse(screen, COLORS['STONE'],
                                      (screen_x + 10, screen_y + 20, 
                                       self.tile_size - 20, self.tile_size - 30))