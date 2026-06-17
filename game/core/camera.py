from game.core.vector import Vector2
from settings import CAMERA_ZOOM

class Camera:
    """Камера, следующая за игроком"""
    
    def __init__(self, world_width, world_height):
        self.position = Vector2(0, 0)
        self.world_width = world_width
        self.world_height = world_height
        self.zoom = CAMERA_ZOOM
    
    def update(self, target, viewport_width, viewport_height):
        """Обновляет позицию камеры, следуя за реальной позицией цели"""
        # Получаем реальный центр игрока (без учета визуального прыжка)
        target_center = target.get_center()  # Используем get_center(), не get_visual_center()
        
        # Центрируем камеру на цели
        visible_width = viewport_width / self.zoom
        visible_height = viewport_height / self.zoom
        target_x = target_center.x - visible_width / 2
        target_y = target_center.y - visible_height / 2
        
        # Ограничиваем камеру границами мира
        max_x = max(0, self.world_width - visible_width)
        max_y = max(0, self.world_height - visible_height)
        self.position.x = max(0, min(target_x, max_x))
        self.position.y = max(0, min(target_y, max_y))
    
    def world_to_screen(self, world_pos):
        """Конвертирует мировые координаты в экранные"""
        return Vector2(
            (world_pos.x - self.position.x) * self.zoom,
            (world_pos.y - self.position.y) * self.zoom
        )

    def screen_to_world(self, screen_x, screen_y):
        return Vector2(
            screen_x / self.zoom + self.position.x,
            screen_y / self.zoom + self.position.y,
        )

    def scale_length(self, value):
        return value * self.zoom
    
    @property
    def x(self):
        return self.position.x
    
    @property
    def y(self):
        return self.position.y
