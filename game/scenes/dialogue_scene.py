import pygame

from game.items import create_item_stack
from game.scenes.base import Scene
from settings import COLORS


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
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 24)
        self.name_font = pygame.font.Font(None, 34)
        self.message = ""
        self.message_timer = 0.0
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
        self._draw_portrait(panel, speaker)
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
        if node is None or self.current_node_id in self.npc.rewarded_nodes:
            return

        rewards = node.get("rewards")
        if not rewards:
            return

        messages = []
        coins = int(rewards.get("coins", 0))
        if coins > 0 and self.player.add_coins(coins):
            messages.append(f"+{coins} coins")

        for raw_item in rewards.get("items", []):
            if isinstance(raw_item, str):
                item_id = raw_item
                quantity = 1
            else:
                item_id = raw_item.get("item_id")
                quantity = int(raw_item.get("quantity", 1))

            item_stack = create_item_stack(item_id, quantity)
            if item_stack is not None and self.player.pickup_item(item_stack=item_stack):
                messages.append(f"{item_stack.name} x{item_stack.quantity}")

        for flag in rewards.get("flags", []):
            if self.player.set_flag(flag):
                messages.append(str(flag))

        self.npc.rewarded_nodes.add(self.current_node_id)
        if messages:
            self.message = "Received: " + ", ".join(messages)
            self.message_timer = 2.0

    def _draw_portrait(self, panel, speaker):
        portrait_size = min(120, panel.height - 80)
        left_rect = pygame.Rect(panel.x + 28, panel.y + 52, portrait_size, portrait_size)
        right_rect = pygame.Rect(panel.right - portrait_size - 28, panel.y + 52, portrait_size, portrait_size)
        rect = left_rect if speaker == "player" else right_rect
        label = "Player" if speaker == "player" else self.npc.name
        fill = COLORS["PLAYER"] if speaker == "player" else self.npc.color

        pygame.draw.rect(self.app.screen, fill, rect, border_radius=10)
        pygame.draw.rect(self.app.screen, COLORS["WHITE"], rect, width=2, border_radius=10)
        name = self.small_font.render(label, True, COLORS["WHITE"])
        self.app.screen.blit(name, name.get_rect(center=(rect.centerx, rect.bottom + 18)))

    def _draw_text(self, panel, node, speaker):
        margin = 180
        text_rect = pygame.Rect(panel.x + margin, panel.y + 50, panel.width - margin * 2, 96)
        speaker_name = "Player" if speaker == "player" else self.npc.name
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
        hint = self.small_font.render("Enter/E - next | 1-9 - choice | Esc - close", True, COLORS["UI_TEXT_DIM"])
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
