import pygame

from game.core.assets import load_image
from game.entities.entity import Entity
from settings import ASSETS_DIR, COLORS


class WorldObject(Entity):
    _LABEL_FONT_CACHE: dict[int, pygame.font.Font] = {}
    _SPRITE_CACHE: dict[tuple[str, int, int], pygame.Surface | None] = {}

    """Базовый объект мира, загружаемый из уровня."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="object",
        color=None,
        is_solid=False,
        is_interactable=False,
        hitbox_width=None,
        hitbox_height=None,
        hitbox_offset_x=0,
        hitbox_offset_y=0,
        interaction_width=None,
        interaction_height=None,
        interaction_offset_x=None,
        interaction_offset_y=None,
        properties=None,
    ):
        super().__init__(
            x,
            y,
            width,
            height,
            hitbox_width=hitbox_width,
            hitbox_height=hitbox_height,
            hitbox_offset_x=hitbox_offset_x,
            hitbox_offset_y=hitbox_offset_y,
            interaction_width=interaction_width,
            interaction_height=interaction_height,
            interaction_offset_x=interaction_offset_x,
            interaction_offset_y=interaction_offset_y,
        )
        self.name = name
        self.color = COLORS["SOLID_OBJECT"] if color is None else color
        self.is_solid = is_solid
        self.is_interactable = is_interactable
        self.properties = {} if properties is None else properties
        self.is_active = False
        self._label_cache_key = None
        self._label_surface = None
        self.sprite_path = self.properties.get("sprite_path")
        self.sprite_scale = max(0.1, float(self.properties.get("sprite_scale", 1.0)))
        self.sprite_anchor = str(self.properties.get("sprite_anchor", "top_left")).strip().lower()
        self.pixel_offset_x = int(self.properties.get("pixel_offset_x", 0))
        self.pixel_offset_y = int(self.properties.get("pixel_offset_y", 0))

    def interact(self, player, game_scene):
        return False

    def update(self, dt, game_scene):
        return None

    def draw(self, screen, camera):
        screen_x = self.position.x - camera.position.x
        screen_y = self.position.y - camera.position.y
        rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        if self._draw_sprite_if_available(screen, rect):
            self.draw_name_label(screen, rect)
            self.draw_debug(screen, camera)
            return
        pygame.draw.rect(
            screen,
            self.color,
            rect,
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            COLORS["BLACK"],
            rect,
            width=2,
            border_radius=6,
        )
        self.draw_name_label(screen, rect)
        self.draw_debug(screen, camera)

    def _draw_sprite_if_available(self, screen, rect):
        sprite = self._get_sprite_surface()
        if sprite is None:
            return False
        draw_x, draw_y = self._get_sprite_draw_position(rect, sprite)
        screen.blit(sprite, (draw_x, draw_y))
        return True

    def _get_sprite_surface(self):
        if not self.sprite_path:
            return None
        draw_size = self._get_sprite_draw_size()
        cache_key = (str(self.sprite_path), int(draw_size[0]), int(draw_size[1]))
        if cache_key not in self._SPRITE_CACHE:
            self._SPRITE_CACHE[cache_key] = load_image(
                ASSETS_DIR / str(self.sprite_path),
                size=draw_size,
            )
        return self._SPRITE_CACHE[cache_key]

    def _get_sprite_draw_size(self):
        return (
            max(1, int(round(self.width * self.sprite_scale))),
            max(1, int(round(self.height * self.sprite_scale))),
        )

    def _get_sprite_draw_position(self, rect, sprite):
        if self.sprite_anchor == "bottom_center":
            return (
                rect.x + (rect.width - sprite.get_width()) / 2 + self.pixel_offset_x,
                rect.y + (rect.height - sprite.get_height()) + self.pixel_offset_y,
            )
        return rect.x + self.pixel_offset_x, rect.y + self.pixel_offset_y

    def draw_name_label(self, screen, rect, text=None):
        if self.sprite_path and not self.properties.get("show_name_with_sprite", False):
            self._label_cache_key = None
            self._label_surface = None
            return
        label = (self.properties.get("display_name") or text or self.name or "").strip()
        if not label:
            self._label_cache_key = None
            self._label_surface = None
            return

        cache_key = (label, rect.width, rect.height)
        if self._label_cache_key != cache_key:
            self._label_surface = self._build_label_surface(label, rect.width, rect.height)
            self._label_cache_key = cache_key
        if self._label_surface is not None:
            screen.blit(self._label_surface, rect.topleft)

    def _build_label_surface(self, label, width, height):
        surface = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)

        max_width = max(18, width - 8)
        max_height = max(16, height - 8)

        best_font = None
        best_lines = None
        best_line_height = 0
        for font_size in range(min(20, max_height), 7, -1):
            font = self._get_label_font(font_size)
            lines = _fit_label_lines(label, font, max_width, max_lines=2)
            if lines is None:
                continue
            line_height = font.get_linesize()
            total_height = line_height * len(lines)
            if total_height <= max_height:
                best_font = font
                best_lines = lines
                best_line_height = line_height
                break

        if best_font is None or best_lines is None:
            return None

        total_height = best_line_height * len(best_lines)
        start_y = (height - total_height) / 2
        for index, line in enumerate(best_lines):
            text_surface = best_font.render(line, True, COLORS["WHITE"])
            outline_surface = best_font.render(line, True, COLORS["BLACK"])
            text_rect = text_surface.get_rect(center=(width / 2, start_y + best_line_height * index + best_line_height / 2))
            for offset_x, offset_y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                surface.blit(outline_surface, text_rect.move(offset_x, offset_y))
            surface.blit(text_surface, text_rect)
        return surface

    @classmethod
    def _get_label_font(cls, font_size):
        font = cls._LABEL_FONT_CACHE.get(font_size)
        if font is None:
            font = pygame.font.Font(None, font_size)
            cls._LABEL_FONT_CACHE[font_size] = font
        return font


def _fit_label_lines(text, font, max_width, max_lines=2):
    words = str(text).split()
    if not words:
        return None

    lines = [words[0]]
    for word in words[1:]:
        candidate = f"{lines[-1]} {word}"
        if font.size(candidate)[0] <= max_width:
            lines[-1] = candidate
            continue
        lines.append(word)
        if len(lines) > max_lines:
            return _truncate_label(text, font, max_width, max_lines)

    if any(font.size(line)[0] > max_width for line in lines):
        return _truncate_label(text, font, max_width, max_lines)
    return lines


def _truncate_label(text, font, max_width, max_lines):
    compact = str(text).replace(" ", "")
    if not compact:
        return None

    if max_lines == 1:
        return [_ellipsize(compact, font, max_width)]

    half = max(1, len(compact) // 2)
    first = _ellipsize(compact[:half], font, max_width)
    second = _ellipsize(compact[half:], font, max_width)
    return [first, second]


def _ellipsize(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text

    trimmed = text
    while trimmed and font.size(trimmed + "...")[0] > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + "...") if trimmed else text[:1]
