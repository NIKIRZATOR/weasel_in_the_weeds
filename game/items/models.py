from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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
class ItemDefinition:
    id: str
    name: str
    kind: ItemKind
    stackable: bool = True
    max_stack: int = 99
    equip_slot: EquipSlot | None = None
    stats: dict[str, int] = field(default_factory=dict)
    price: int = 0
    icon_path: str | None = None
    description: str = ""


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
        return self.definition.name

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
