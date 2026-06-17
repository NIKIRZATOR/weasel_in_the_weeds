from game.core.vector import Vector2

class Camera:
    """Камера, следующая за игроком"""
    
    def __init__(self, world_width, world_height):
        self.position = Vector2(0, 0)
        self.world_width = world_width
        self.world_height = world_height
    
    def update(self, target, viewport_width, viewport_height):
        """Обновляет позицию камеры, следуя за реальной позицией цели"""
        # Получаем реальный центр игрока (без учета визуального прыжка)
        target_center = target.get_center()  # Используем get_center(), не get_visual_center()
        
        # Центрируем камеру на цели
        target_x = target_center.x - viewport_width // 2
        target_y = target_center.y - viewport_height // 2
        
        # Ограничиваем камеру границами мира
        max_x = max(0, self.world_width - viewport_width)
        max_y = max(0, self.world_height - viewport_height)
        self.position.x = max(0, min(target_x, max_x))
        self.position.y = max(0, min(target_y, max_y))
    
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
