class CollisionSystem:
    """Система обработки коллизий по физическому хитбоксу сущности."""

    def __init__(self, tilemap):
        self.tilemap = tilemap

    def check_collision(self, x, y, entity, ignore_jump=False):
        hitbox_x, hitbox_y, hitbox_width, hitbox_height = entity.get_hitbox_at(x, y)
        corners = [
            (hitbox_x, hitbox_y),
            (hitbox_x + hitbox_width - 1, hitbox_y),
            (hitbox_x, hitbox_y + hitbox_height - 1),
            (hitbox_x + hitbox_width - 1, hitbox_y + hitbox_height - 1),
        ]

        for cx, cy in corners:
            tile_x = int(cx // self.tilemap.tile_size)
            tile_y = int(cy // self.tilemap.tile_size)

            if not self.tilemap.is_walkable(tile_x, tile_y, ignore_jump):
                return True

        return False
