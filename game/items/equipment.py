from __future__ import annotations

from game.items.models import CharacterStats, ItemStack
from game.items.types import EquipSlot


class Equipment:
    def __init__(self):
        self.slots: dict[EquipSlot, ItemStack | None] = {
            EquipSlot.HELMET: None,
            EquipSlot.CHEST: None,
            EquipSlot.BOOTS: None,
            EquipSlot.WEAPON: None,
            EquipSlot.ACCESSORY_1: None,
            EquipSlot.ACCESSORY_2: None,
        }

    def get(self, slot: EquipSlot) -> ItemStack | None:
        return self.slots.get(slot)

    def can_equip_stack_to_slot(self, stack: ItemStack, slot: EquipSlot) -> bool:
        if stack.equip_slot is None:
            return False
        if stack.equip_slot == EquipSlot.ACCESSORY:
            return slot in (EquipSlot.ACCESSORY_1, EquipSlot.ACCESSORY_2)
        return stack.equip_slot == slot

    def equip_stack_to_slot(self, stack: ItemStack, slot: EquipSlot) -> ItemStack | None:
        if not self.can_equip_stack_to_slot(stack, slot):
            return None
        previous = self.slots.get(slot)
        self.slots[slot] = stack
        return previous

    def unequip_slot(self, slot: EquipSlot) -> ItemStack | None:
        previous = self.slots.get(slot)
        self.slots[slot] = None
        return previous

    def get_stat_bonuses(self) -> CharacterStats:
        bonuses = CharacterStats()
        for stack in self.slots.values():
            if stack is None:
                continue
            bonuses = bonuses + CharacterStats.from_mapping(stack.definition.stats)
        return bonuses

    def has_equipped(self, item_id: str) -> bool:
        return any(stack is not None and stack.item_id == item_id for stack in self.slots.values())
