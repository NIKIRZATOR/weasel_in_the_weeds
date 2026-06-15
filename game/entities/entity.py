from game.core.vector import Vector2

class Entity:
    """Базовый класс для всех игровых объектов"""
    
    def __init__(self, x, y, width, height):
        self.position = Vector2(x, y)
        self.width = width
        self.height = height
        self.velocity = Vector2(0, 0)
    
    def get_rect(self):
        """Возвращает прямоугольник для коллизий"""
        return (self.position.x, self.position.y, self.width, self.height)
    
    def get_center(self):
        """Возвращает центр объекта"""
        return Vector2(
            self.position.x + self.width / 2,
            self.position.y + self.height / 2
        )
    
    def update(self, dt):
        """Обновление состояния (будет переопределено)"""
        pass
    
    def draw(self, screen, camera):
        """Отрисовка (будет переопределено)"""
        pass