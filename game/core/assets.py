from pathlib import Path

import pygame


def load_image(path: str | Path, size: tuple[int, int] | None = None) -> pygame.Surface | None:
    image_path = Path(path)
    if not image_path.exists():
        return None

    image = pygame.image.load(str(image_path)).convert_alpha()
    if size is not None:
        image = pygame.transform.scale(image, size)

    return image
