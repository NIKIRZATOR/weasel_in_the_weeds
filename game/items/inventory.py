from __future__ import annotations

from game.items.catalog import get_item_definition
from game.items.models import ItemDefinition, ItemStack


class Inventory:
    def __init__(self, capacity: int = 24):
        self.capacity = capacity
        self.slots: list[ItemStack | None] = [None] * capacity

    def get_stack_at(self, index: int) -> ItemStack | None:
        if 0 <= index < self.capacity:
            return self.slots[index]
        return None

    def set_stack_at(self, index: int, stack: ItemStack | None) -> bool:
        if not 0 <= index < self.capacity:
            return False
        self.slots[index] = stack
        return True

    def swap_slots(self, first: int, second: int) -> bool:
        if not (0 <= first < self.capacity and 0 <= second < self.capacity):
            return False
        self.slots[first], self.slots[second] = self.slots[second], self.slots[first]
        return True

    def clear_slot(self, index: int) -> ItemStack | None:
        if not 0 <= index < self.capacity:
            return None
        stack = self.slots[index]
        self.slots[index] = None
        return stack

    def find_first_empty_slot(self) -> int | None:
        for index, stack in enumerate(self.slots):
            if stack is None:
                return index
        return None

    def find_item(self, item_id: str) -> tuple[int, ItemStack] | None:
        for index, stack in enumerate(self.slots):
            if stack is not None and stack.item_id == item_id:
                return index, stack
        return None

    def count_item(self, item_id: str) -> int:
        total = 0
        for stack in self.slots:
            if stack is not None and stack.item_id == item_id:
                total += stack.quantity
        return total

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        return self.count_item(item_id) >= quantity

    def _resolve_stack(self, item_or_stack, quantity: int = 1) -> ItemStack | None:
        if isinstance(item_or_stack, ItemStack):
            return item_or_stack.copy(quantity if quantity != 1 else item_or_stack.quantity)
        if isinstance(item_or_stack, ItemDefinition):
            return ItemStack(item_or_stack, quantity)
        if isinstance(item_or_stack, str):
            definition = get_item_definition(item_or_stack)
            if definition is None:
                return None
            return ItemStack(definition, quantity)
        return None

    def can_add_item(self, item_or_stack, quantity: int = 1) -> bool:
        stack = self._resolve_stack(item_or_stack, quantity)
        if stack is None:
            return False

        remaining = stack.quantity
        if stack.stackable:
            for slot in self.slots:
                if slot is not None and slot.item_id == stack.item_id:
                    remaining -= slot.available_space()
                    if remaining <= 0:
                        return True

        empty_slots = sum(1 for slot in self.slots if slot is None)
        if stack.stackable:
            needed_slots = (remaining + stack.max_stack - 1) // stack.max_stack
        else:
            needed_slots = remaining
        return empty_slots >= needed_slots

    def add_item(self, item_or_stack, quantity: int = 1) -> bool:
        stack = self._resolve_stack(item_or_stack, quantity)
        if stack is None:
            return False

        if not self.can_add_item(stack):
            return False

        remaining = stack.quantity
        if stack.stackable:
            for slot in self.slots:
                if slot is not None and slot.item_id == stack.item_id and slot.available_space() > 0:
                    to_add = min(slot.available_space(), remaining)
                    slot.quantity += to_add
                    remaining -= to_add
                    if remaining <= 0:
                        return True

        while remaining > 0:
            empty_slot = self.find_first_empty_slot()
            if empty_slot is None:
                return False
            if stack.stackable:
                amount = min(stack.max_stack, remaining)
            else:
                amount = 1
            self.slots[empty_slot] = stack.copy(amount)
            remaining -= amount

        return True

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        if quantity <= 0:
            return False
        if not self.has_item(item_id, quantity):
            return False

        remaining = quantity
        for index, stack in enumerate(self.slots):
            if stack is None or stack.item_id != item_id:
                continue

            removed = stack.consume(remaining)
            remaining -= removed
            if stack.quantity <= 0:
                self.slots[index] = None
            if remaining <= 0:
                return True

        return False

    def iter_stacks(self):
        for index, stack in enumerate(self.slots):
            yield index, stack
