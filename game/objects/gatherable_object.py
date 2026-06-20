from __future__ import annotations

import random

from game.items import create_item_stack
from game.objects.world_object import WorldObject
from settings import COLORS


class GatherableObject(WorldObject):
    def __init__(self, x, y, width, height, name="gatherable_object", properties=None):
        properties = {} if properties is None else properties
        color = tuple(properties.get("color", COLORS["INTERACTABLE_OBJECT"]))
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            color=color,
            is_solid=bool(properties.get("solid", False)),
            is_interactable=True,
            properties=properties,
        )
        self.is_gatherable = True
        self.base_color = color
        self.depleted_color = tuple(properties.get("depleted_color", COLORS["UI_SLOT_BORDER"]))
        self.loot = list(properties.get("loot", []))
        self.one_time = bool(properties.get("one_time", True))
        self.is_depleted = bool(properties.get("depleted", False))
        if self.is_depleted:
            self.color = self.depleted_color

    def interact(self, player, game_scene):
        if self.is_depleted:
            game_scene.last_interaction_message = self.properties.get(
                "depleted_text",
                f"{self.name} is empty.",
            )
            game_scene.last_interaction_timer = 1.5
            return False

        rewards = []
        for reward in self._roll_loot():
            item_stack = create_item_stack(reward["item_id"], reward["quantity"])
            if item_stack is None:
                continue
            if not player.pickup_item(item_stack=item_stack):
                game_scene.last_interaction_message = "Inventory is full."
                game_scene.last_interaction_timer = 1.5
                return False
            rewards.append(item_stack)

        knowledge_shards = max(0, int(self.properties.get("knowledge_shards", 0)))
        if knowledge_shards > 0:
            player.add_knowledge_shards(knowledge_shards)

        if not rewards and knowledge_shards <= 0:
            game_scene.last_interaction_message = self.properties.get(
                "empty_text",
                f"You found nothing in {self.name}.",
            )
            game_scene.last_interaction_timer = 1.5
            if self.one_time:
                self._deplete()
            return False

        if self.one_time:
            self._deplete()

        reward_text = ", ".join(f"{stack.name} x{stack.quantity}" for stack in rewards[:3])
        if len(rewards) > 3:
            reward_text += ", ..."
        if knowledge_shards > 0:
            if reward_text:
                reward_text = f"{reward_text} + {knowledge_shards} shards"
            else:
                reward_text = f"{knowledge_shards} shards"
        game_scene.last_interaction_message = f"Gathered: {reward_text}"
        game_scene.last_interaction_timer = 1.5
        return True

    def _roll_loot(self):
        rolled = []
        for raw_reward in self.loot:
            chance = float(raw_reward.get("chance", 1.0))
            if random.random() > chance:
                continue
            minimum = max(1, int(raw_reward.get("min_quantity", raw_reward.get("quantity", 1))))
            maximum = max(minimum, int(raw_reward.get("max_quantity", raw_reward.get("quantity", minimum))))
            rolled.append(
                {
                    "item_id": raw_reward["item_id"],
                    "quantity": random.randint(minimum, maximum),
                }
            )
        return rolled

    def _deplete(self):
        self.is_depleted = True
        self.color = self.depleted_color
