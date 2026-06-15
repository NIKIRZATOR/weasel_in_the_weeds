from game.objects.world_object import WorldObject
from settings import COLORS


class InteractableObject(WorldObject):
    """Объект мира, который реагирует на нажатие E."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="interactable_object",
        is_solid=False,
        properties=None,
    ):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=COLORS["INTERACTABLE_OBJECT"],
            is_solid=is_solid,
            is_interactable=True,
            properties=properties,
        )

    def interact(self, player, game_scene):
        self.is_active = not self.is_active
        self.color = (
            COLORS["INTERACTABLE_ACTIVE"]
            if self.is_active
            else COLORS["INTERACTABLE_OBJECT"]
        )
        game_scene.last_interaction_message = f"Взаимодействие: {self.name}"
        game_scene.last_interaction_timer = 1.5
        return True
