import pygame

from game.core.assets import load_image
from settings import BASE_DIR


class AnimatedMenuBackground:
    def __init__(
        self,
        *,
        image_path=None,
        crop_ratio=2 / 3,
        pan_seconds=20.0,
        blur_divisor=6,
        overlay_color=(10, 12, 18, 120),
    ):
        self.background_image = load_image(image_path or (BASE_DIR / "game" / "scenes" / "background_image_menu.png"))
        self.crop_ratio = crop_ratio
        self.pan_seconds = pan_seconds
        self.blur_divisor = blur_divisor
        self.overlay_color = overlay_color
        self.pan_direction = 1
        self.pan_x = 0.0
        self.pan_min_x = 0.0
        self.pan_max_x = 0.0
        self.crop_rect = None
        self.recalculate()

    def recalculate(self):
        if self.background_image is None:
            self.crop_rect = None
            return

        image_width, image_height = self.background_image.get_size()
        crop_width = max(1, int(image_width * self.crop_ratio))
        crop_height = max(1, int(image_height * self.crop_ratio))
        crop_x = max(0, (image_width - crop_width) // 2)
        crop_y = max(0, (image_height - crop_height) // 2)

        self.pan_min_x = 0.0
        self.pan_max_x = float(max(0, image_width - crop_width))
        self.pan_x = min(max(float(crop_x), self.pan_min_x), self.pan_max_x)
        self.pan_direction = 1
        self.crop_rect = pygame.Rect(int(self.pan_x), crop_y, crop_width, crop_height)

    def update(self, dt):
        if self.background_image is None or self.crop_rect is None:
            return

        travel_range = self.pan_max_x - self.pan_min_x
        if travel_range <= 0:
            return

        speed = travel_range / max(self.pan_seconds, 0.001)
        self.pan_x += self.pan_direction * speed * dt

        if self.pan_x >= self.pan_max_x:
            self.pan_x = self.pan_max_x
            self.pan_direction = -1
        elif self.pan_x <= self.pan_min_x:
            self.pan_x = self.pan_min_x
            self.pan_direction = 1

        self.crop_rect.x = int(round(self.pan_x))

    def draw(self, screen, fallback_color=(18, 18, 26)):
        screen_width, screen_height = screen.get_size()
        if self.background_image is None or self.crop_rect is None:
            screen.fill(fallback_color)
            return

        background_frame = self.background_image.subsurface(self.crop_rect)
        scaled_background = pygame.transform.smoothscale(background_frame, (screen_width, screen_height))

        if self.blur_divisor > 1:
            blur_size = (
                max(1, screen_width // self.blur_divisor),
                max(1, screen_height // self.blur_divisor),
            )
            scaled_background = pygame.transform.smoothscale(
                pygame.transform.smoothscale(scaled_background, blur_size),
                (screen_width, screen_height),
            )

        screen.blit(scaled_background, (0, 0))

        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill(self.overlay_color)
        screen.blit(overlay, (0, 0))
