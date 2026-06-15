from settings import TILE_SIZE

class CollisionSystem:
    """Система обработки коллизий"""
    
    def __init__(self, tilemap):
        self.tilemap = tilemap
    
    def check_collision(self, x, y, entity, ignore_jump=False):
        """Проверяет коллизию для сущности"""
        corners = [
            (x, y),
            (x + entity.width, y),
            (x, y + entity.height),
            (x + entity.width, y + entity.height)
        ]
        
        for cx, cy in corners:
            tile_x = int(cx // TILE_SIZE)
            tile_y = int(cy // TILE_SIZE)
            
            if not self.tilemap.is_walkable(tile_x, tile_y, ignore_jump):
                return True
        
        return False