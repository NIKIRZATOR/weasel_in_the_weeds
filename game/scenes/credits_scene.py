from __future__ import annotations

import pygame

from game.core.assets import load_image
from game.scenes.base import Scene
from settings import ASSETS_DIR, COLORS


class CreditsScene(Scene):
    SCROLL_SPEED = 48
    START_OFFSET = 80
    SECTION_GAP = 38
    BLOCK_GAP = 72
    PANEL_PADDING_X = 36

    def __init__(self, app):
        self.app = app
        self.title_font = pygame.font.Font(None, 74)
        self.section_font = pygame.font.Font(None, 42)
        self.body_font = pygame.font.Font(None, 34)
        self.hint_font = pygame.font.Font(None, 26)
        self.background = load_image(ASSETS_DIR / "system" / "map_background.png")
        self.scroll_y = 0.0
        self.credits_lines = self._build_credits_lines()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    self._close()

    def update(self, dt):
        self.scroll_y += self.SCROLL_SPEED * dt

    def draw(self):
        screen = self.app.screen
        screen_width, screen_height = self.app.get_screen_size()
        self._draw_background(screen, screen_width, screen_height)

        panel_rect = pygame.Rect(
            max(24, screen_width // 7),
            0,
            min(screen_width - 48, max(420, screen_width - screen_width // 3)),
            screen_height,
        )
        self.app.draw_translucent_panel(panel_rect, (10, 12, 18), alpha=156)

        center_x = screen_width // 2
        current_y = screen_height + self.START_OFFSET - self.scroll_y
        max_text_width = max(120, panel_rect.width - self.PANEL_PADDING_X * 2)
        previous_clip = screen.get_clip()
        screen.set_clip(panel_rect)
        for line in self.credits_lines:
            wrapped_lines = _wrap_text(line["text"], line["font"], max_text_width)
            for wrapped_line in wrapped_lines:
                surface = line["font"].render(wrapped_line, True, line["color"])
                rect = surface.get_rect(center=(center_x, int(current_y)))
                screen.blit(surface, rect)
                current_y += surface.get_height() + 6
            current_y += max(0, line["gap"] - 6)
        screen.set_clip(previous_clip)

        vignette = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 84))
        screen.blit(vignette, (0, 0))

        self._draw_fade_masks(screen, screen_width, screen_height)
        self._draw_hint(screen, screen_width, screen_height)

    def _draw_background(self, screen, screen_width, screen_height):
        if self.background is not None:
            scaled = pygame.transform.smoothscale(self.background, (screen_width, screen_height))
            screen.blit(scaled, (0, 0))
            return
        screen.fill((18, 24, 30))

    def _draw_fade_masks(self, screen, screen_width, screen_height):
        fade_height = max(80, screen_height // 6)
        top_fade = pygame.Surface((screen_width, fade_height), pygame.SRCALPHA)
        bottom_fade = pygame.Surface((screen_width, fade_height), pygame.SRCALPHA)
        for index in range(fade_height):
            alpha = int(255 * (1 - index / max(1, fade_height - 1)))
            pygame.draw.line(top_fade, (0, 0, 0, alpha), (0, index), (screen_width, index))
            pygame.draw.line(
                bottom_fade,
                (0, 0, 0, alpha),
                (0, fade_height - index - 1),
                (screen_width, fade_height - index - 1),
            )
        screen.blit(top_fade, (0, 0))
        screen.blit(bottom_fade, (0, screen_height - fade_height))

    def _draw_hint(self, screen, screen_width, screen_height):
        hint = "Нажмите Enter или Esc, чтобы выйти"
        text = self.hint_font.render(hint, True, (220, 226, 236))
        hint_bg = pygame.Surface((text.get_width() + 24, text.get_height() + 12), pygame.SRCALPHA)
        hint_bg.fill((8, 10, 16, 165))
        hint_rect = hint_bg.get_rect(center=(screen_width // 2, screen_height - 28))
        screen.blit(hint_bg, hint_rect.topleft)
        screen.blit(text, text.get_rect(center=hint_rect.center))

    def _build_credits_lines(self):
        return [
            {"text": "Weasel in the Weeds", "font": self.title_font, "color": COLORS["WHITE"], "gap": self.BLOCK_GAP},
            {"text": "Конец текущей версии", "font": self.section_font, "color": (214, 221, 204), "gap": self.BLOCK_GAP},
            {"text": "Спасибо за игру", "font": self.section_font, "color": (236, 230, 188), "gap": self.SECTION_GAP},
            {"text": "Это только начало пути.", "font": self.body_font, "color": (228, 228, 228), "gap": self.SECTION_GAP},
            {"text": "История семьи ласок продолжается.", "font": self.body_font, "color": (228, 228, 228), "gap": self.BLOCK_GAP},
            {"text": "О проекте", "font": self.section_font, "color": (198, 232, 220), "gap": self.SECTION_GAP},
            {"text": "Игра разработана в рамках хакатона Kodik LaunchPad.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "Этот проект стал возможностью наконец начать делать игру,", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "которую давно хотелось создать, но постоянно находились причины отложить.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "С помощью инструментов компании Kodik и их среды разработки", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "эта идея превратилась в живой игровой прототип.", "font": self.body_font, "color": (230, 230, 230), "gap": self.BLOCK_GAP},
            {"text": "Сюжет и мир", "font": self.section_font, "color": (198, 232, 220), "gap": self.SECTION_GAP},
            {"text": "Семья ласок попала в ураган, и один из ее членов оказался потерян.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "Главный герой приходит в себя в незнакомом месте", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "и отправляется на поиски своей семьи, прокладывая путь вперед.", "font": self.body_font, "color": (230, 230, 230), "gap": self.BLOCK_GAP},
            {"text": "Автор сюжета и мира", "font": self.section_font, "color": (198, 232, 220), "gap": self.SECTION_GAP},
            {"text": "Соло-разработчик", "font": self.body_font, "color": (230, 230, 230), "gap": self.BLOCK_GAP},
            {"text": "Разработка", "font": self.section_font, "color": (198, 232, 220), "gap": self.SECTION_GAP},
            {"text": "Проект создан на Python с использованием Pygame.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "Карты уровней собирались в Tiled.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "Спрайты и часть визуальных материалов создавались в Aseprite.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "В проекте реализованы боевая система, квесты, диалоги, триггеры, боссы,", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "музыка, звуковые события, крафт и исследование мира.", "font": self.body_font, "color": (230, 230, 230), "gap": self.BLOCK_GAP},
            {"text": "Благодарности авторам звука и музыки", "font": self.section_font, "color": (198, 232, 220), "gap": self.SECTION_GAP},
            {"text": "Искренняя благодарность авторам, которые бесплатно поделились", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "музыкой и звуковыми эффектами с сообществом разработчиков игр.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "Благодаря вашему труду игровой мир стал живее, атмосфернее и выразительнее.", "font": self.body_font, "color": (230, 230, 230), "gap": self.BLOCK_GAP},
            {"text": "Отдельная благодарность:", "font": self.body_font, "color": (236, 230, 188), "gap": self.SECTION_GAP},
            {"text": "rgbin — за Knight & Monsters Sounds Pack.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "Clutch Assets — за 200+ Free RPG Sounds.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "alkakrab — за Free Fantasy Medieval Ambient Music Pack", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "и Free 25 Fantasy RPG Game Tracks Vol. 2.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "Nebula Audio — за Character Footsteps Rock & Grass Pack.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "TheAmbientFort — за RPG Maker's Kit 1.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "Leohpaz — за RPG Essentials SFX Free", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "и MiniFantasy Dungeon SFX Pack.", "font": self.body_font, "color": (230, 230, 230), "gap": self.BLOCK_GAP},
            {"text": "Спасибо за творчество, профессионализм и поддержку", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "независимых разработчиков. Ваш вклад помог сделать проект", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "более качественным, атмосферным и по-настоящему живым.", "font": self.body_font, "color": (230, 230, 230), "gap": self.BLOCK_GAP},
            {"text": "Отдельная благодарность", "font": self.section_font, "color": (198, 232, 220), "gap": self.SECTION_GAP},
            {"text": "Kodik LaunchPad за повод начать.", "font": self.body_font, "color": (230, 230, 230), "gap": self.SECTION_GAP},
            {"text": "И всем, кто играет, тестирует и поддерживает проект.", "font": self.body_font, "color": (230, 230, 230), "gap": self.BLOCK_GAP},
            {"text": "Продолжение следует...", "font": self.body_font, "color": (245, 236, 192), "gap": self.BLOCK_GAP},
        ]

    def _close(self):
        from game.scenes.menu_scene import MenuScene

        self.app.set_scene(MenuScene(self.app))


def _wrap_text(text, font, max_width):
    words = str(text).split()
    if not words:
        return [""]

    lines = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        if font.size(candidate)[0] <= max_width:
            current_line = candidate
            continue
        lines.append(current_line)
        current_line = word
    lines.append(current_line)
    return lines
