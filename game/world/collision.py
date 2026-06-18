class CollisionSystem:
    """Система обработки коллизий по физическому хитбоксу сущности."""

    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.objects = []

    def set_objects(self, objects):
        self.objects = objects

    def check_collision(self, x, y, entity, ignore_jump=False):
        if getattr(entity, "has_collision_circle", lambda: False)():
            return self._check_circle_collision(x, y, entity, ignore_jump)

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

    def _check_circle_collision(self, x, y, entity, ignore_jump=False):
        circle = entity.get_collision_circle_at(x, y)
        if circle is None:
            return False

        center_x, center_y, radius = circle
        tile_size = self.tilemap.tile_size
        min_tile_x = int((center_x - radius) // tile_size)
        max_tile_x = int((center_x + radius) // tile_size)
        min_tile_y = int((center_y - radius) // tile_size)
        max_tile_y = int((center_y + radius) // tile_size)

        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                if self.tilemap.is_walkable(tile_x, tile_y, ignore_jump):
                    continue
                rect_x = tile_x * tile_size
                rect_y = tile_y * tile_size
                if _circle_rects_intersect(center_x, center_y, radius, rect_x, rect_y, tile_size, tile_size):
                    return True

        if self._circle_collides_with_solid_object(center_x, center_y, radius, entity):
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

    def _circle_collides_with_solid_object(self, center_x, center_y, radius, moving_entity):
        for world_object in self.objects:
            if world_object is moving_entity or not world_object.is_solid:
                continue

            other_x, other_y, other_width, other_height = world_object.get_hitbox_rect()
            if _circle_rects_intersect(
                center_x,
                center_y,
                radius,
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


def _circle_rects_intersect(circle_x, circle_y, radius, rect_x, rect_y, rect_width, rect_height):
    closest_x = max(rect_x, min(circle_x, rect_x + rect_width))
    closest_y = max(rect_y, min(circle_y, rect_y + rect_height))
    dx = circle_x - closest_x
    dy = circle_y - closest_y
    return dx * dx + dy * dy < radius * radius
