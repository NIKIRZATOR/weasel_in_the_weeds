from __future__ import annotations

from dataclasses import dataclass, field


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
