import pygame

from game.objects.world_object import WorldObject
from settings import COLORS


class LevelTransition(WorldObject):
    def __init__(self, x, y, width, height, name="level_transition", properties=None):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=(90, 130, 230),
            is_solid=False,
            is_interactable=False,
            properties=properties,
        )
        self.is_transition = True

    def can_activate(self, player):
        return (
            self._has_required_items(player)
            and self._has_required_coins(player)
            and self._has_required_flags(player)
        )

    def get_block_message(self):
        return self.properties.get("blocked_message", "The path is blocked.")

    def get_target_level(self):
        return self.properties.get("target_level")

    def get_target_spawn(self):
        spawn = self.properties.get("target_spawn")
        if not spawn:
            return None
        return int(spawn.get("x", 0)), int(spawn.get("y", 0))

    def get_flags_to_set(self):
        return [str(flag) for flag in self.properties.get("set_flags", []) if flag]

    def _has_required_items(self, player):
        required_items = self.properties.get("required_items", [])
        for requirement in required_items:
            if isinstance(requirement, str):
                item_id = requirement
                quantity = 1
            else:
                item_id = requirement.get("item_id")
                quantity = int(requirement.get("quantity", 1))

            if not item_id or not player.has_item(item_id, quantity):
                return False
        return True

    def _has_required_coins(self, player):
        required_coins = int(self.properties.get("required_coins", 0))
        return player.coins >= required_coins

    def _has_required_flags(self, player):
        required_flags = self.properties.get("required_flags", [])
        return player.has_flags(required_flags)

    def draw(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        rect = pygame.Rect(screen_x, screen_y, self.width, self.height)

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((90, 130, 230, 70))
        screen.blit(overlay, rect.topleft)
        pygame.draw.rect(screen, COLORS["WHITE"], rect, width=2, border_radius=6)
        self.draw_name_label(screen, rect)
        self.draw_debug(screen, camera)
