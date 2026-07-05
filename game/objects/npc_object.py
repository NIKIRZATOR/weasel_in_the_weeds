import pygame

from game.core.assets import load_image
from game.dialogues import load_dialogue
from game.objects.world_object import WorldObject
from settings import ASSETS_DIR, COLORS


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
        self.persistence_id = self._build_persistence_id(properties)
        self.animation_frames = self._load_animation_frames(properties)
        self.animation_frame_duration = max(0.05, float(properties.get("animation_frame_duration", 0.16)))
        self.animation_frame_timer = 0.0
        self.animation_frame_index = 0

    def update(self, dt, game_scene):
        if len(self.animation_frames) <= 1:
            return
        self.animation_frame_timer += dt
        while self.animation_frame_timer >= self.animation_frame_duration:
            self.animation_frame_timer -= self.animation_frame_duration
            self.animation_frame_index = (self.animation_frame_index + 1) % len(self.animation_frames)

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

    def _build_persistence_id(self, properties):
        explicit_id = properties.get("npc_id")
        if explicit_id:
            return str(explicit_id)

        dialogue_file = properties.get("dialogue_file")
        if dialogue_file:
            return f"dialogue:{dialogue_file}"

        return f"name:{self.name}:{int(self.position.x)}:{int(self.position.y)}"

    def _load_animation_frames(self, properties):
        sprite_sheet_path = properties.get("sprite_sheet_path")
        frame_count = int(properties.get("animation_frame_count", 0))
        frame_width = int(properties.get("animation_frame_width", 64))
        frame_height = int(properties.get("animation_frame_height", 64))
        if not sprite_sheet_path or frame_count <= 0:
            return []
        sheet = load_image(ASSETS_DIR / str(sprite_sheet_path))
        if sheet is None:
            return []
        target_size = (int(self.width), int(self.height))
        frames = []
        for index in range(frame_count):
            source_rect = pygame.Rect(index * frame_width, 0, frame_width, frame_height)
            if source_rect.right > sheet.get_width() or source_rect.bottom > sheet.get_height():
                break
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), source_rect)
            if target_size != (frame_width, frame_height):
                frame = pygame.transform.scale(frame, target_size)
            frames.append(frame)
        return frames

    def draw(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        if self.animation_frames:
            sprite = self.animation_frames[self.animation_frame_index % len(self.animation_frames)]
            screen.blit(sprite, rect.topleft)
            self.draw_name_label(screen, rect)
            self.draw_debug(screen, camera)
            return
        if self._draw_sprite_if_available(screen, rect):
            self.draw_name_label(screen, rect)
            self.draw_debug(screen, camera)
            return

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
        self.draw_name_label(screen, rect)
        self.draw_debug(screen, camera)
