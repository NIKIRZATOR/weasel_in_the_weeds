from __future__ import annotations

from dataclasses import dataclass, field

from game.localization import get_localizer


@dataclass(frozen=True)
class RecipeIngredient:
    item_id: str
    quantity: int = 1


@dataclass(frozen=True)
class RecipeResult:
    item_id: str
    quantity: int = 1


@dataclass(frozen=True)
class RecipeDefinition:
    id: str
    name: str
    category: str
    description: str = ""
    result: RecipeResult = field(default_factory=RecipeResult)
    ingredients: tuple[RecipeIngredient, ...] = ()
    unlock_type: str = "default"
    knowledge_cost: int = 0
    required_flags: tuple[str, ...] = ()
    sort_order: int = 0

    def is_default_unlocked(self) -> bool:
        return self.unlock_type == "default"

    def localized_name(self) -> str:
        localizer = get_localizer()
        key = f"recipes.{self.id}.name"
        translated = localizer.t(key)
        return translated if translated != key else self.name

    def localized_description(self) -> str:
        localizer = get_localizer()
        key = f"recipes.{self.id}.description"
        translated = localizer.t(key)
        return translated if translated != key else self.description
