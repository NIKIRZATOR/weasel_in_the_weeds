from pathlib import Path

import pygame

from game.core.assets import load_image
from game.items import create_item_stack
from game.localization import get_localizer
from game.scenes.base import Scene
from settings import ASSETS_DIR, COLORS, PLAYER_PORTRAIT_SPRITE


class DialogueScene(Scene):
    def __init__(self, app, game_scene, npc):
        self.app = app
        self.game_scene = game_scene
        self.player = game_scene.player
        self.npc = npc
        self.dialogue = npc.dialogue
        self.nodes = self.dialogue.get("nodes", {})
        self.current_node_id = self.dialogue.get("start")
        self.selected_choice = 0
        self.localizer = get_localizer()
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 24)
        self.name_font = pygame.font.Font(None, 34)
        self.message = ""
        self.message_timer = 0.0
        self._portrait_cache = {}
        self._apply_current_node_rewards()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._close()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                    self._advance()
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._move_choice(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._move_choice(1)
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    self._choose_by_number(event.key - pygame.K_1)

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0.0:
                self.message = ""

    def draw(self):
        self.game_scene.draw()
        screen_width, screen_height = self.app.get_screen_size()
        panel = pygame.Rect(0, screen_height // 2, screen_width, screen_height // 2)
        overlay = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        overlay.fill((16, 16, 24, 238))
        self.app.screen.blit(overlay, panel.topleft)
        pygame.draw.line(self.app.screen, COLORS["UI_SLOT_BORDER"], panel.topleft, panel.topright, 2)

        node = self._current_node()
        if node is None:
            self._close()
            return

        speaker = node.get("speaker", "npc")
        self._draw_portrait(panel, node, speaker)
        self._draw_text(panel, node, speaker)
        self._draw_choices(panel, node)
        self._draw_hint(panel)

        if self.message:
            text = self.small_font.render(self.message, True, (255, 220, 120))
            self.app.screen.blit(text, text.get_rect(center=(screen_width // 2, panel.y + 24)))

    def _current_node(self):
        if self.current_node_id is None:
            return None
        return self.nodes.get(self.current_node_id)

    def _advance(self):
        node = self._current_node()
        if node is None:
            self._close()
            return

        choices = node.get("choices", [])
        if choices:
            self._select_choice(self.selected_choice)
            return

        next_node = node.get("next")
        if next_node:
            self._go_to_node(next_node)
        else:
            self._close()

    def _move_choice(self, direction):
        node = self._current_node()
        if node is None:
            return
        choices = node.get("choices", [])
        if not choices:
            return
        self.selected_choice = (self.selected_choice + direction) % len(choices)

    def _choose_by_number(self, index):
        node = self._current_node()
        if node is None:
            return
        choices = node.get("choices", [])
        if 0 <= index < len(choices):
            self._select_choice(index)

    def _select_choice(self, index):
        node = self._current_node()
        if node is None:
            return
        choices = node.get("choices", [])
        if not 0 <= index < len(choices):
            return
        choice = choices[index]
        next_node = choice.get("next")
        if next_node:
            self._go_to_node(next_node)
        else:
            self._close()

    def _go_to_node(self, node_id):
        self.current_node_id = node_id
        self.selected_choice = 0
        self._apply_current_node_rewards()

    def _apply_current_node_rewards(self):
        node = self._current_node()
        if node is None:
            return

        npc_key = self.npc.persistence_id
        if self.player.has_claimed_dialogue_reward(npc_key, self.current_node_id):
            return

        rewards = node.get("rewards")
        if not rewards:
            return

        messages = []
        coins = int(rewards.get("coins", 0))
        if coins > 0 and self.player.add_coins(coins):
            messages.append(f"+{coins} {self.localizer.t('ui.inventory.stat_coins').lower()}")
        knowledge_shards = int(rewards.get("knowledge_shards", 0))
        if knowledge_shards > 0 and self.player.add_knowledge_shards(knowledge_shards):
            messages.append(f"+{knowledge_shards} {self.localizer.t('ui.inventory.stat_shards').lower()}")

        for raw_item in rewards.get("items", []):
            if isinstance(raw_item, str):
                item_id = raw_item
                quantity = 1
            else:
                item_id = raw_item.get("item_id")
                quantity = int(raw_item.get("quantity", 1))

            item_stack = create_item_stack(item_id, quantity)
            if item_stack is not None and self.player.pickup_item(item_stack=item_stack):
                if item_stack.kind.value == "currency":
                    messages.append(f"+{item_stack.quantity} {item_stack.name}")
                else:
                    messages.append(f"{item_stack.name} x{item_stack.quantity}")

        for flag in rewards.get("flags", []):
            if self.player.set_flag(flag):
                messages.append(str(flag))

        self.player.mark_dialogue_reward_claimed(npc_key, self.current_node_id)
        if messages:
            self.message = self.localizer.t("ui.dialogue.received", items=", ".join(messages))
            self.message_timer = 2.0

    def _draw_portrait(self, panel, node, speaker):
        portrait_size = min(135, max(105, panel.height - 96))
        left_rect = pygame.Rect(panel.x + 24, panel.y + 28, portrait_size, portrait_size)
        right_rect = pygame.Rect(panel.right - portrait_size - 24, panel.y + 28, portrait_size, portrait_size)
        rect = left_rect if speaker == "player" else right_rect
        label = self.localizer.t("ui.dialogue.player_name") if speaker == "player" else self.npc.name
        fill = COLORS["PLAYER"] if speaker == "player" else self.npc.color

        portrait = self._get_portrait_surface(node, speaker, portrait_size)
        if portrait is not None:
            self.app.screen.blit(portrait, rect.topleft)
        else:
            pygame.draw.rect(self.app.screen, fill, rect, border_radius=10)
        name = self.small_font.render(label, True, COLORS["WHITE"])
        self.app.screen.blit(name, name.get_rect(center=(rect.centerx, rect.bottom + 18)))

    def _get_portrait_surface(self, node, speaker, portrait_size):
        portrait_path = self._resolve_portrait_path(node, speaker)
        if portrait_path is None:
            return None

        cache_key = (portrait_path, portrait_size)
        if cache_key not in self._portrait_cache:
            surface = load_image(portrait_path)
            if surface is not None:
                surface = self._fit_portrait_to_square(surface, portrait_size)
            self._portrait_cache[cache_key] = surface
        return self._portrait_cache[cache_key]

    def _resolve_portrait_path(self, node, speaker):
        node_portrait = str(node.get("portrait_path", "")).strip()
        if node_portrait:
            return self._resolve_asset_path(node_portrait)

        if speaker == "player":
            return PLAYER_PORTRAIT_SPRITE

        npc_portrait = str(self.npc.properties.get("portrait_path", "")).strip()
        if npc_portrait:
            return self._resolve_asset_path(npc_portrait)
        return None

    def _resolve_asset_path(self, raw_path):
        path = Path(raw_path)
        if path.is_absolute():
            return path
        return ASSETS_DIR / path

    def _fit_portrait_to_square(self, surface, portrait_size):
        width = surface.get_width()
        height = surface.get_height()
        if width <= 0 or height <= 0:
            return surface

        if width != portrait_size or height != portrait_size:
            scale = min(portrait_size / width, portrait_size / height)
            scaled_size = (
                max(1, int(round(width * scale))),
                max(1, int(round(height * scale))),
            )
            surface = pygame.transform.smoothscale(surface, scaled_size)

        result = pygame.Surface((portrait_size, portrait_size), pygame.SRCALPHA)
        offset_x = (portrait_size - surface.get_width()) // 2
        offset_y = (portrait_size - surface.get_height()) // 2
        result.blit(surface, (offset_x, offset_y))
        return result

    def _draw_text(self, panel, node, speaker):
        margin = 230
        text_rect = pygame.Rect(panel.x + margin, panel.y + 48, panel.width - margin * 2, 110)
        speaker_name = self.localizer.t("ui.dialogue.player_name") if speaker == "player" else self.npc.name
        name = self.name_font.render(speaker_name, True, COLORS["WHITE"])
        self.app.screen.blit(name, (text_rect.x, text_rect.y - 30))

        lines = _wrap_text(node.get("text", ""), self.font, text_rect.width)
        for index, line in enumerate(lines[:4]):
            rendered = self.font.render(line, True, COLORS["WHITE"])
            self.app.screen.blit(rendered, (text_rect.x, text_rect.y + index * 28))

    def _draw_choices(self, panel, node):
        choices = node.get("choices", [])
        if not choices:
            return

        start_y = panel.y + panel.height - 118
        start_x = panel.x + 180
        width = panel.width - 360
        for index, choice in enumerate(choices[:4]):
            selected = index == self.selected_choice
            color = COLORS["UI_SLOT_SELECTED"] if selected else COLORS["UI_TEXT_DIM"]
            prefix = f"{index + 1}. "
            text = self.small_font.render(prefix + choice.get("text", "..."), True, color)
            self.app.screen.blit(text, (start_x, start_y + index * 26))
            if selected:
                pygame.draw.rect(
                    self.app.screen,
                    COLORS["UI_SLOT_SELECTED"],
                    (start_x - 10, start_y + index * 26 - 2, width, 24),
                    width=1,
                    border_radius=4,
                )

    def _draw_hint(self, panel):
        hint = self.small_font.render(self.localizer.t("ui.dialogue.close_hint"), True, COLORS["UI_TEXT_DIM"])
        self.app.screen.blit(hint, (panel.right - hint.get_width() - 18, panel.bottom - 28))

    def _close(self):
        self.app.set_scene(self.game_scene)


def _wrap_text(text, font, max_width):
    words = str(text).split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines
