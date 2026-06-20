from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from game.localization import get_localizer
from game.items.types import EquipSlot, ItemKind


@dataclass(frozen=True)
class CharacterStats:
    max_health: int = 0
    max_stamina: int = 0
    attack: int = 0
    defense: int = 0
    speed: int = 0

    @classmethod
    def from_mapping(cls, values: dict[str, int] | None) -> "CharacterStats":
        if not values:
            return cls()
        return cls(
            max_health=int(values.get("max_health", 0)),
            max_stamina=int(values.get("max_stamina", 0)),
            attack=int(values.get("attack", 0)),
            defense=int(values.get("defense", 0)),
            speed=int(values.get("speed", 0)),
        )

    def __add__(self, other: "CharacterStats") -> "CharacterStats":
        return CharacterStats(
            max_health=self.max_health + other.max_health,
            max_stamina=self.max_stamina + other.max_stamina,
            attack=self.attack + other.attack,
            defense=self.defense + other.defense,
            speed=self.speed + other.speed,
        )


@dataclass(frozen=True)
class WeaponAttackProfile:
    damage_bonus: int = 1
    damage_multiplier: float = 1.0
    range: float = 40.0
    thickness: int = 42
    duration: float = 0.2
    cooldown: float = 0.1
    stamina_cost: float = 2.0
    is_ranged: bool = False
    projectile_speed: float = 320.0
    projectile_radius: int = 5
    projectile_distance: float = 520.0


@dataclass(frozen=True)
class ItemDefinition:
    id: str
    name: str
    kind: ItemKind
    stackable: bool = True
    max_stack: int = 99
    equip_slot: EquipSlot | None = None
    stats: dict[str, int] = field(default_factory=dict)
    inventory_capacity_bonus: int = 0
    price: int = 0
    icon_path: str | None = None
    wallet_key: str | None = None
    description: str = ""
    weapon_class: str | None = None
    attack_profiles: dict[str, WeaponAttackProfile] = field(default_factory=dict)

    def localized_name(self) -> str:
        localizer = get_localizer()
        key = f"items.{self.id}.name"
        translated = localizer.t(key)
        return translated if translated != key else self.name

    def localized_description(self) -> str:
        localizer = get_localizer()
        key = f"items.{self.id}.description"
        translated = localizer.t(key)
        return translated if translated != key else self.description

    def get_attack_profile(self, attack_kind: str) -> WeaponAttackProfile | None:
        return self.attack_profiles.get(str(attack_kind))


@dataclass
class ItemStack:
    definition: ItemDefinition
    quantity: int = 1

    def __post_init__(self):
        self.quantity = max(1, int(self.quantity))
        if not self.definition.stackable:
            self.quantity = 1
        else:
            self.quantity = min(self.quantity, self.definition.max_stack)

    @property
    def item_id(self) -> str:
        return self.definition.id

    @property
    def name(self) -> str:
        return self.definition.localized_name()

    @property
    def description(self) -> str:
        return self.definition.localized_description()

    @property
    def kind(self) -> ItemKind:
        return self.definition.kind

    @property
    def equip_slot(self) -> EquipSlot | None:
        return self.definition.equip_slot

    @property
    def stackable(self) -> bool:
        return self.definition.stackable

    @property
    def max_stack(self) -> int:
        return self.definition.max_stack

    def copy(self, quantity: int | None = None) -> "ItemStack":
        return ItemStack(self.definition, self.quantity if quantity is None else quantity)

    def can_stack_with(self, other: "ItemStack") -> bool:
        return self.definition.id == other.definition.id and self.stackable and other.stackable

    def available_space(self) -> int:
        if not self.stackable:
            return 0
        return max(0, self.max_stack - self.quantity)

    def is_full(self) -> bool:
        return not self.stackable or self.quantity >= self.max_stack

    def consume(self, quantity: int = 1) -> int:
        removed = min(self.quantity, max(0, quantity))
        self.quantity -= removed
        return removed

    def to_payload(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "quantity": self.quantity,
        }
