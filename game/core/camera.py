from game.core.vector import Vector2
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class Camera:
    """Камера, следующая за игроком"""
    
    def __init__(self, world_width, world_height):
        self.position = Vector2(0, 0)
        self.world_width = world_width
        self.world_height = world_height
    
    def update(self, target):
        """Обновляет позицию камеры, следуя за реальной позицией цели"""
        # Получаем реальный центр игрока (без учета визуального прыжка)
        target_center = target.get_center()  # Используем get_center(), не get_visual_center()
        
        # Центрируем камеру на цели
        target_x = target_center.x - SCREEN_WIDTH // 2
        target_y = target_center.y - SCREEN_HEIGHT // 2
        
        # Ограничиваем камеру границами мира
        self.position.x = max(0, min(target_x, self.world_width - SCREEN_WIDTH))
        self.position.y = max(0, min(target_y, self.world_height - SCREEN_HEIGHT))
    
    def world_to_screen(self, world_pos):
        """Конвертирует мировые координаты в экранные"""
        return Vector2(
            world_pos.x - self.position.x,
            world_pos.y - self.position.y
        )
    
    @property
    def x(self):
        return self.position.x
    
    @property
    def y(self):
        return self.position.y