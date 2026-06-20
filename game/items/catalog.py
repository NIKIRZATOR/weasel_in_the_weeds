from __future__ import annotations

import json
from pathlib import Path

import pygame

from game.core.assets import load_image
from game.items.models import ItemDefinition, ItemStack, WeaponAttackProfile
from game.items.types import EquipSlot, ItemKind
from settings import ASSETS_DIR


CATALOG_PATH = Path(__file__).with_name("catalog_data.json")
_ICON_CACHE: dict[tuple[str, tuple[int, int]], pygame.Surface | None] = {}


def _load_item_definitions() -> dict[str, ItemDefinition]:
    raw_catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    definitions: dict[str, ItemDefinition] = {}

    for item_id, raw_item in raw_catalog.items():
        kind = ItemKind(raw_item["kind"])
        equip_slot_value = raw_item.get("equip_slot")
        equip_slot = EquipSlot(equip_slot_value) if equip_slot_value else None
        definitions[item_id] = ItemDefinition(
            id=item_id,
            name=raw_item.get("name", item_id),
            kind=kind,
            stackable=bool(raw_item.get("stackable", True)),
            max_stack=int(raw_item.get("max_stack", 99)),
            equip_slot=equip_slot,
            stats={key: int(value) for key, value in raw_item.get("stats", {}).items()},
            inventory_capacity_bonus=int(raw_item.get("inventory_capacity_bonus", 0)),
            price=int(raw_item.get("price", 0)),
            icon_path=raw_item.get("icon_path"),
            wallet_key=raw_item.get("wallet_key"),
            description=raw_item.get("description", ""),
            weapon_class=raw_item.get("weapon_class"),
            attack_profiles={
                str(attack_kind): WeaponAttackProfile(
                    damage_bonus=int(raw_profile.get("damage_bonus", 1)),
                    damage_multiplier=float(raw_profile.get("damage_multiplier", 1.0)),
                    range=float(raw_profile.get("range", 40.0)),
                    thickness=int(raw_profile.get("thickness", 42)),
                    duration=float(raw_profile.get("duration", 0.2)),
                    cooldown=float(raw_profile.get("cooldown", 0.1)),
                    stamina_cost=float(raw_profile.get("stamina_cost", 2.0)),
                    is_ranged=bool(raw_profile.get("is_ranged", False)),
                    projectile_speed=float(raw_profile.get("projectile_speed", 320.0)),
                    projectile_radius=int(raw_profile.get("projectile_radius", 5)),
                    projectile_distance=float(raw_profile.get("projectile_distance", 520.0)),
                )
                for attack_kind, raw_profile in raw_item.get("attack_profiles", {}).items()
            },
        )

    return definitions


ITEM_DEFINITIONS: dict[str, ItemDefinition] = _load_item_definitions()


def get_item_definition(item_id: str) -> ItemDefinition | None:
    return ITEM_DEFINITIONS.get(item_id)


def create_item_stack(item_id: str, quantity: int = 1) -> ItemStack | None:
    definition = get_item_definition(item_id)
    if definition is None:
        return None
    return ItemStack(definition, quantity)


def get_item_icon(item_or_definition: str | ItemDefinition | None, size: tuple[int, int]) -> pygame.Surface | None:
    if item_or_definition is None:
        return None

    if isinstance(item_or_definition, ItemDefinition):
        definition = item_or_definition
    else:
        definition = get_item_definition(str(item_or_definition))

    if definition is None or not definition.icon_path:
        return None

    cache_key = (definition.icon_path, size)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    icon = load_image(ASSETS_DIR / definition.icon_path, size=size)
    _ICON_CACHE[cache_key] = icon
    return icon
