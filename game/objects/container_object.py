from __future__ import annotations

import random

from game.items import Inventory, create_item_stack, get_item_definition
from game.objects.interactable_object import InteractableObject
from settings import COLORS


CONTAINER_CAPACITIES = {
    "crate": 5,
    "chest": 8,
    "large_chest": 10,
}

CONTAINER_COLORS = {
    "crate": (145, 103, 62),
    "chest": (166, 116, 55),
    "large_chest": (184, 132, 61),
}


class ContainerObject(InteractableObject):
    """Interactive world container with persistent, optionally random contents."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="container",
        is_solid=True,
        properties=None,
    ):
        properties = {} if properties is None else dict(properties)
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            is_solid=is_solid,
            properties=properties,
        )
        self.container_type = str(properties.get("container_type", "chest"))
        if self.container_type not in CONTAINER_CAPACITIES:
            raise ValueError(f"Unknown container type: {self.container_type}")

        self.inventory = Inventory(CONTAINER_CAPACITIES[self.container_type])
        self.fixed_items = tuple(properties.get("fixed_items", ()))
        self.random_loot = properties.get("random_loot") or {}
        self.contents_generated = False
        self.object_id = str(properties.get("object_id", ""))
        self._state_store = None
        self._state_key = None
        self.color = CONTAINER_COLORS[self.container_type]
        self.is_container = True

    def bind_state_store(self, state_store, state_key):
        self._state_store = state_store
        self._state_key = str(state_key)
        payload = state_store.get(self._state_key)
        if payload is not None:
            self._load_state(payload)

    def generate_contents(self):
        if self.contents_generated:
            return

        for item in self.fixed_items:
            self._add_configured_item(item, strict=True)

        entries = tuple(self.random_loot.get("entries", ()))
        rolls = max(0, int(self.random_loot.get("rolls", 0)))
        for entry in entries:
            item_id = str(entry.get("item_id", ""))
            if get_item_definition(item_id) is None:
                raise ValueError(f"Unknown item '{item_id}' in container '{self.name}'")
        weighted_entries = [entry for entry in entries if float(entry.get("weight", 1)) > 0]
        weights = [float(entry.get("weight", 1)) for entry in weighted_entries]
        for _ in range(rolls):
            if not weighted_entries:
                break
            entry = random.choices(weighted_entries, weights=weights, k=1)[0]
            chance = max(0.0, min(1.0, float(entry.get("chance", 1.0))))
            if random.random() > chance:
                continue
            minimum = max(1, int(entry.get("min_quantity", 1)))
            maximum = max(minimum, int(entry.get("max_quantity", minimum)))
            generated = dict(entry)
            generated["quantity"] = random.randint(minimum, maximum)
            self._add_configured_item(generated, strict=False)

        self.contents_generated = True
        self.save_state()

    def _add_configured_item(self, item, strict):
        item_id = str(item.get("item_id", ""))
        quantity = max(1, int(item.get("quantity", 1)))
        definition = get_item_definition(item_id)
        if definition is None:
            raise ValueError(f"Unknown item '{item_id}' in container '{self.name}'")

        remaining = quantity
        added_any = False
        while remaining > 0:
            chunk_size = 1 if not definition.stackable else min(definition.max_stack, remaining)
            stack = create_item_stack(item_id, chunk_size)
            if stack is None or not self.inventory.add_item(stack):
                if strict:
                    raise ValueError(f"Fixed contents do not fit in container '{self.name}'")
                break
            remaining -= chunk_size
            added_any = True
        return added_any

    def interact(self, player, game_scene):
        self.generate_contents()
        self.is_active = True
        self.color = COLORS["INTERACTABLE_ACTIVE"]
        game_scene.open_container(self)
        return True

    def close(self):
        self.is_active = False
        self.color = CONTAINER_COLORS[self.container_type]
        self.save_state()

    def save_state(self):
        if self._state_store is None or self._state_key is None:
            return
        self._state_store[self._state_key] = {
            "contents_generated": self.contents_generated,
            "slots": [stack.to_payload() if stack is not None else None for stack in self.inventory.slots],
        }

    def _load_state(self, payload):
        self.contents_generated = bool(payload.get("contents_generated", False))
        for index, raw_stack in enumerate(payload.get("slots", ())):
            if index >= self.inventory.capacity or raw_stack is None:
                continue
            stack = create_item_stack(raw_stack.get("item_id", ""), raw_stack.get("quantity", 1))
            if stack is not None:
                self.inventory.set_stack_at(index, stack)
