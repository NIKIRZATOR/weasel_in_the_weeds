import pygame

from game.localization import get_localizer
from game.scenes.base import Scene
from settings import COLORS


class PauseMenuScene(Scene):
    def __init__(self, app, game_scene):
        self.app = app
        self.game_scene = game_scene
        self.localizer = get_localizer()
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 28)
        self.buttons = []
        self.message = ""
        self.message_timer = 0.0
        self._layout_size = None
        self._build_buttons()

    def _build_buttons(self):
        screen_width, screen_height = self.app.get_screen_size()
        button_width = 320
        button_height = 48
        gap = 14
        labels = [
            (self.localizer.t("ui.pause.resume"), self.resume_game, False),
            (self.localizer.t("ui.pause.inventory"), self.open_inventory, False),
            #(self.localizer.t("ui.pause.quests"), self.open_quest_log, False),
            #(self.localizer.t("ui.pause.progression"), self.open_progression, False),
            (self.localizer.t("ui.pause.settings"), self.open_settings, False),
            (self.localizer.t("ui.pause.exit_to_menu"), self.exit_to_menu, False),
        ]

        title_gap = 58
        title_height = self.title_font.get_height()
        buttons_height = len(labels) * button_height + max(0, len(labels) - 1) * gap
        content_height = title_height + title_gap + buttons_height
        content_top = max(40, (screen_height - content_height) // 2)
        self.title_center_y = content_top + title_height // 2
        start_y = content_top + title_height + title_gap

        self.buttons = []
        for index, (label, action, disabled) in enumerate(labels):
            rect = pygame.Rect(
                (screen_width - button_width) // 2,
                start_y + index * (button_height + gap),
                button_width,
                button_height,
            )
            self.buttons.append(
                {
                    "rect": rect,
                    "label": label,
                    "action": action,
                    "disabled": disabled,
                }
            )
        self._layout_size = self.app.get_screen_size()

    def _ensure_layout(self):
        if self._layout_size != self.app.get_screen_size():
            self._build_buttons()

    def on_language_changed(self):
        self._build_buttons()

    def resume_game(self):
        self.app.set_scene(self.game_scene)

    def open_inventory(self):
        from game.scenes.inventory_scene import InventoryScene

        self.app.set_scene(InventoryScene(self.app, self.game_scene))

    def open_settings(self):
        from game.scenes.settings_scene import SettingsScene

        self.app.set_scene(SettingsScene(self.app, self, overlay_scene=self.game_scene))

    def open_progression(self):
        from game.scenes.progression_scene import ProgressionScene

        self.app.set_scene(ProgressionScene(self.app, self.game_scene))

    def open_quest_log(self):
        from game.scenes.quest_log_scene import QuestLogScene

        self.app.set_scene(QuestLogScene(self.app, self.game_scene))

    def exit_to_menu(self):
        from game.scenes.menu_scene import MenuScene
        from game.scenes.splash_scene import SplashScene

        self.game_scene.save_progress(reason="menu_exit")
        self.app.set_scene(
            SplashScene(
                self.app,
                lambda: MenuScene(self.app),
                title=self.localizer.t("ui.common.saving"),
                background=(20, 20, 20),
            )
        )

    def handle_events(self, events):
        self._ensure_layout()
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.resume_game()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_k:
                from game.scenes.crafting_scene import CraftingScene

                self.app.set_scene(CraftingScene(self.app, self.game_scene))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_j:
                self.open_quest_log()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_o:
                self.open_progression()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    if not button["disabled"] and button["rect"].collidepoint(mouse_pos):
                        button["action"]()
                        break

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0.0:
                self.message = ""

    def draw(self):
        self._ensure_layout()
        screen_width, screen_height = self.app.get_screen_size()
        self.game_scene.draw()

        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.app.screen.blit(overlay, (0, 0))

        title = self.title_font.render(self.localizer.t("ui.pause.title"), True, COLORS["WHITE"])
        self.app.screen.blit(title, title.get_rect(center=(screen_width // 2, self.title_center_y)))

        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            rect = button["rect"]
            hovered = rect.collidepoint(mouse_pos)

            fill = (55, 55, 65)
            border = (100, 100, 120)
            if hovered:
                fill = (75, 75, 95)
                border = (120, 180, 255)

            pygame.draw.rect(self.app.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=8)

            label = self.button_font.render(button["label"], True, COLORS["WHITE"])
            self.app.screen.blit(label, label.get_rect(center=rect.center))
        if self.message:
            message = self.info_font.render(self.message, True, (255, 220, 120))
            self.app.screen.blit(
                message,
                message.get_rect(center=(screen_width // 2, screen_height - 105)),
            )
