class CollisionSystem:
    """Система обработки коллизий по физическому хитбоксу сущности."""

    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.objects = []

    def set_objects(self, objects):
        self.objects = objects

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

        if self._collides_with_solid_object(hitbox_x, hitbox_y, hitbox_width, hitbox_height, entity):
            return True

        return False

    def _collides_with_solid_object(self, hitbox_x, hitbox_y, hitbox_width, hitbox_height, moving_entity):
        for world_object in self.objects:
            if world_object is moving_entity or not world_object.is_solid:
                continue

            other_x, other_y, other_width, other_height = world_object.get_hitbox_rect()
            if _rects_intersect(
                hitbox_x,
                hitbox_y,
                hitbox_width,
                hitbox_height,
                other_x,
                other_y,
                other_width,
                other_height,
            ):
                return True

        return False


def _rects_intersect(ax, ay, aw, ah, bx, by, bw, bh):
    return (
        ax < bx + bw
        and ax + aw > bx
        and ay < by + bh
        and ay + ah > by
    )
