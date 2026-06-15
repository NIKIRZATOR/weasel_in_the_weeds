import math

class Vector2:
    """2D вектор для удобной работы с координатами"""
    
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def normalize(self):
        length = self.length()
        if length > 0:
            return Vector2(self.x / length, self.y / length)
        return Vector2(0, 0)
    
    def length(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def length_squared(self):
        return self.x**2 + self.y**2
    
    def tuple(self):
        return (self.x, self.y)