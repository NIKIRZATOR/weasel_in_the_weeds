from __future__ import annotations

import json
from pathlib import Path

from game.crafting.models import RecipeDefinition, RecipeIngredient, RecipeResult


CATALOG_PATH = Path(__file__).with_name("recipes_data.json")


def _load_recipe_catalog() -> dict[str, RecipeDefinition]:
    raw_catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    recipes: dict[str, RecipeDefinition] = {}
    for recipe_id, raw_recipe in raw_catalog.items():
        ingredients = tuple(
            RecipeIngredient(
                item_id=str(raw_ingredient["item_id"]),
                quantity=max(1, int(raw_ingredient.get("quantity", 1))),
            )
            for raw_ingredient in raw_recipe.get("ingredients", [])
        )
        raw_result = raw_recipe["result"]
        recipes[recipe_id] = RecipeDefinition(
            id=recipe_id,
            name=str(raw_recipe.get("name", recipe_id)),
            category=str(raw_recipe.get("category", "other")),
            description=str(raw_recipe.get("description", "")),
            result=RecipeResult(
                item_id=str(raw_result["item_id"]),
                quantity=max(1, int(raw_result.get("quantity", 1))),
            ),
            ingredients=ingredients,
            unlock_type=str(raw_recipe.get("unlock_type", "default")),
            knowledge_cost=max(0, int(raw_recipe.get("knowledge_cost", 0))),
            required_flags=tuple(str(flag) for flag in raw_recipe.get("required_flags", [])),
            sort_order=int(raw_recipe.get("sort_order", 0)),
        )
    return recipes


RECIPE_DEFINITIONS = _load_recipe_catalog()


def get_recipe_definition(recipe_id: str) -> RecipeDefinition | None:
    return RECIPE_DEFINITIONS.get(recipe_id)


def get_recipe_definitions() -> list[RecipeDefinition]:
    return sorted(
        RECIPE_DEFINITIONS.values(),
        key=lambda recipe: (recipe.category, recipe.sort_order, recipe.name.lower()),
    )
