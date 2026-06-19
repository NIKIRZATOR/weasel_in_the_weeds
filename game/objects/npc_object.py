import pygame

from game.dialogues import load_dialogue
from game.objects.world_object import WorldObject
from settings import COLORS


class NpcObject(WorldObject):
    def __init__(self, x, y, width, height, name="npc_object", properties=None):
        properties = {} if properties is None else properties
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=properties.get("color", (165, 125, 90)),
            is_solid=bool(properties.get("solid", False)),
            is_interactable=True,
            properties=properties,
        )
        self.is_npc = True
        self.max_health = max(1, int(properties.get("health", 30)))
        self.health = self.max_health
        self.dialogue_error = None
        self.dialogue = self._load_dialogue(properties)
        self.rewarded_nodes = set()

    def interact(self, player, game_scene):
        if not self.dialogue:
            game_scene.last_interaction_message = self.dialogue_error or f"{self.name} has nothing to say."
            game_scene.last_interaction_timer = 1.5
            return False

        from game.scenes.dialogue_scene import DialogueScene

        game_scene.app.set_scene(DialogueScene(game_scene.app, game_scene, self))
        return True

    def _load_dialogue(self, properties):
        if properties.get("dialogue"):
            return properties["dialogue"]

        dialogue_file = properties.get("dialogue_file")
        if not dialogue_file:
            return None

        try:
            return load_dialogue(dialogue_file)
        except (OSError, ValueError) as error:
            self.dialogue_error = f"Dialogue load failed: {dialogue_file}"
            print(f"{self.dialogue_error}: {error}")
            return None

    def draw(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        rect = pygame.Rect(screen_x, screen_y, self.width, self.height)

        pygame.draw.rect(screen, self.color, rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["BLACK"], rect, width=2, border_radius=10)

        eye_y = screen_y + self.height * 0.35
        pygame.draw.circle(screen, COLORS["BLACK"], (int(screen_x + self.width * 0.35), int(eye_y)), 3)
        pygame.draw.circle(screen, COLORS["BLACK"], (int(screen_x + self.width * 0.65), int(eye_y)), 3)

        health_ratio = self.health / self.max_health
        bar_rect = pygame.Rect(screen_x, screen_y - 10, self.width, 5)
        pygame.draw.rect(screen, COLORS["HEALTH_BG"], bar_rect, border_radius=2)
        pygame.draw.rect(
            screen,
            COLORS["HEALTH"],
            (bar_rect.x, bar_rect.y, bar_rect.width * health_ratio, bar_rect.height),
            border_radius=2,
        )
        self.draw_debug(screen, camera)
