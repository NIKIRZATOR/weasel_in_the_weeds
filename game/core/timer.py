class Timer:
    """Универсальный таймер для игровых событий"""
    
    def __init__(self, duration):
        self.duration = duration
        self.current = 0
        self.active = False
    
    def start(self):
        self.active = True
        self.current = self.duration
    
    def update(self, dt):
        if self.active:
            self.current -= dt
            if self.current <= 0:
                self.active = False
                return True
        return False
    
    def is_active(self):
        return self.active
    
    def get_progress(self):
        """Возвращает прогресс от 0 до 1"""
        if self.duration <= 0:
            return 1
        return 1 - (self.current / self.duration)