from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from game.effects import ActiveEffect
from game.items import create_item_stack
from game.items.models import ItemStack


SAVE_VERSION = 3
SUPPORTED_SAVE_VERSIONS = {2, SAVE_VERSION}
SAVE_ROOT_DIR_NAME = "saves"
INDEX_FILE_NAME = "index.json"
SAVE_FILE_NAME = "save.json"
APP_SETTINGS_FILE_NAME = "settings.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_save_root() -> Path:
    return Path.home() / ".weasel_in_the_weeds" / SAVE_ROOT_DIR_NAME


def serialize_item_stack(stack: ItemStack | None) -> dict[str, Any] | None:
    if stack is None:
        return None
    return {
        "item_id": stack.item_id,
        "quantity": stack.quantity,
    }


def deserialize_item_stack(data: dict[str, Any] | None) -> ItemStack | None:
    if data is None:
        return None
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)
    if not item_id:
        return None
    return create_item_stack(item_id, quantity)


def serialize_inventory(inventory) -> list[dict[str, Any] | None]:
    return [serialize_item_stack(stack) for stack in inventory.slots]


def deserialize_inventory(inventory, data: list[dict[str, Any] | None]) -> None:
    inventory.slots = [None] * inventory.capacity
    for index, slot_data in enumerate(data):
        if index >= inventory.capacity:
            break
        inventory.slots[index] = deserialize_item_stack(slot_data)


def serialize_equipment(equipment) -> dict[str, dict[str, Any] | None]:
    result = {}
    for slot, stack in equipment.slots.items():
        result[slot.value] = serialize_item_stack(stack)
    return result


def deserialize_equipment(equipment, data: dict[str, dict[str, Any] | None]) -> None:
    from game.items.types import EquipSlot

    for slot in list(equipment.slots):
        equipment.slots[slot] = None
    for slot_value, stack_data in data.items():
        try:
            slot = EquipSlot(slot_value)
        except ValueError:
            continue
        equipment.slots[slot] = deserialize_item_stack(stack_data)


def serialize_active_effects(effects: list[ActiveEffect]) -> list[dict[str, Any]]:
    return [
        {
            "effect_type": effect.effect_type.value,
            "value": effect.value,
            "duration": effect.duration,
            "remaining": effect.remaining,
            "source_item_id": effect.source_item_id,
        }
        for effect in effects
    ]


def deserialize_active_effects(data: list[dict[str, Any]]) -> list[ActiveEffect]:
    effects: list[ActiveEffect] = []
    for raw_effect in data:
        effect_type = raw_effect.get("effect_type")
        if not effect_type:
            continue
        try:
            effect = ActiveEffect.create(
                effect_type,
                raw_effect.get("value", 0.0),
                raw_effect.get("duration", raw_effect.get("remaining", 0.0)),
                source_item_id=raw_effect.get("source_item_id"),
            )
        except ValueError:
            continue
        effect.remaining = max(0.0, float(raw_effect.get("remaining", effect.duration)))
        effects.append(effect)
    return effects


def _serialize_level_states(level_states: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    serialized: dict[str, dict[str, Any]] = {}
    for level_key, state in level_states.items():
        serialized[str(level_key)] = {
            "picked_object_ids": sorted(str(value) for value in state.get("picked_object_ids", set())),
            "depleted_object_ids": sorted(str(value) for value in state.get("depleted_object_ids", set())),
            "activated_checkpoint_ids": sorted(str(value) for value in state.get("activated_checkpoint_ids", set())),
            "defeated_enemy_ids": sorted(str(value) for value in state.get("defeated_enemy_ids", set())),
            "active_checkpoint_id": state.get("active_checkpoint_id"),
        }
    return serialized


def _deserialize_level_states(raw_level_states: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    level_states: dict[str, dict[str, Any]] = {}
    for level_key, state in raw_level_states.items():
        level_states[str(level_key)] = {
            "picked_object_ids": set(str(value) for value in state.get("picked_object_ids", [])),
            "depleted_object_ids": set(str(value) for value in state.get("depleted_object_ids", [])),
            "activated_checkpoint_ids": set(str(value) for value in state.get("activated_checkpoint_ids", [])),
            "defeated_enemy_ids": set(str(value) for value in state.get("defeated_enemy_ids", [])),
            "active_checkpoint_id": state.get("active_checkpoint_id"),
        }
    return level_states


def _serialize_quest_progress(quest_progress: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    serialized: dict[str, dict[str, Any]] = {}
    for quest_id, quest_state in quest_progress.items():
        if not isinstance(quest_state, dict):
            continue
        serialized_objectives: dict[str, dict[str, Any]] = {}
        for objective_id, objective_state in quest_state.get("objectives", {}).items():
            if not isinstance(objective_state, dict):
                continue
            serialized_objectives[str(objective_id)] = {
                "current": max(0, int(objective_state.get("current", 0))),
                "required": max(1, int(objective_state.get("required", 1))),
                "completed": bool(objective_state.get("completed", False)),
            }
        serialized[str(quest_id)] = {
            "started": bool(quest_state.get("started", False)),
            "completed": bool(quest_state.get("completed", False)),
            "activation_shown": bool(quest_state.get("activation_shown", False)),
            "objectives": serialized_objectives,
        }
    return serialized


def _deserialize_quest_progress(raw_quest_progress: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    deserialized: dict[str, dict[str, Any]] = {}
    for quest_id, quest_state in raw_quest_progress.items():
        if not isinstance(quest_state, dict):
            continue
        objectives: dict[str, dict[str, Any]] = {}
        for objective_id, objective_state in quest_state.get("objectives", {}).items():
            if not isinstance(objective_state, dict):
                continue
            objectives[str(objective_id)] = {
                "current": max(0, int(objective_state.get("current", 0))),
                "required": max(1, int(objective_state.get("required", 1))),
                "completed": bool(objective_state.get("completed", False)),
            }
        deserialized[str(quest_id)] = {
            "started": bool(quest_state.get("started", False)),
            "completed": bool(quest_state.get("completed", False)),
            "activation_shown": bool(quest_state.get("activation_shown", False)),
            "objectives": objectives,
        }
    return deserialized


def serialize_player_state(player) -> dict[str, Any]:
    return {
        "position": {
            "x": player.position.x,
            "y": player.position.y,
        },
        "spawn_position": {
            "x": player.spawn_position.x,
            "y": player.spawn_position.y,
        },
        "health": player.health,
        "stamina": player.stamina,
        "level": player.level,
        "xp": player.xp,
        "skill_points": player.skill_points,
        "coins": player.coins,
        "knowledge_shards": player.knowledge_shards,
        "selected_hotbar_index": player.selected_hotbar_index,
        "unlocked_skill_ids": sorted(player.unlocked_skill_ids),
        "story_flags": sorted(player.story_flags),
        "quest_progress": _serialize_quest_progress(player.quest_progress),
        "unlocked_recipe_ids": sorted(player.unlocked_recipe_ids),
        "awarded_xp_sources": sorted(player.awarded_xp_sources),
        "explored_tiles_by_level": {
            level: [[bool(cell) for cell in row] for row in tiles]
            for level, tiles in player.explored_tiles_by_level.items()
        },
        "container_states": player.container_states,
        "claimed_dialogue_rewards_by_npc": {
            npc: sorted(nodes)
            for npc, nodes in player.claimed_dialogue_rewards_by_npc.items()
        },
        "level_states": _serialize_level_states(player.level_states),
        "inventory": serialize_inventory(player.inventory),
        "quest_inventory": serialize_inventory(player.quest_inventory),
        "equipment": serialize_equipment(player.equipment),
        "hotbar_slots": [serialize_item_stack(stack) for stack in player.hotbar_slots],
        "active_effects": serialize_active_effects(player.active_effects),
    }


def load_player_state(player, player_data: dict[str, Any]) -> None:
    position = player_data.get("position", {})
    player.position.x = position.get("x", player.position.x)
    player.position.y = position.get("y", player.position.y)

    spawn_position = player_data.get("spawn_position", {})
    player.spawn_position.x = spawn_position.get("x", player.spawn_position.x)
    player.spawn_position.y = spawn_position.get("y", player.spawn_position.y)

    player.level = player_data.get("level", player.level)
    player.xp = player_data.get("xp", player.xp)
    player.skill_points = player_data.get("skill_points", player.skill_points)
    player.coins = player_data.get("coins", player.coins)
    player.knowledge_shards = player_data.get("knowledge_shards", player.knowledge_shards)
    player.unlocked_skill_ids = set(player_data.get("unlocked_skill_ids", []))
    player.story_flags = set(player_data.get("story_flags", []))
    player.quest_progress = _deserialize_quest_progress(player_data.get("quest_progress", {}))
    player.unlocked_recipe_ids = set(player_data.get("unlocked_recipe_ids", []))
    player.awarded_xp_sources = set(player_data.get("awarded_xp_sources", []))
    player.explored_tiles_by_level = {
        level: [[bool(cell) for cell in row] for row in tiles]
        for level, tiles in player_data.get("explored_tiles_by_level", {}).items()
    }
    player.container_states = player_data.get("container_states", {})
    player.claimed_dialogue_rewards_by_npc = {
        npc: set(nodes)
        for npc, nodes in player_data.get("claimed_dialogue_rewards_by_npc", {}).items()
    }
    player.level_states = _deserialize_level_states(player_data.get("level_states", {}))

    deserialize_equipment(player.equipment, player_data.get("equipment", {}))
    player._sync_inventory_capacities()
    deserialize_inventory(player.inventory, player_data.get("inventory", []))
    deserialize_inventory(player.quest_inventory, player_data.get("quest_inventory", []))

    player.hotbar_slots = [None] * len(player.hotbar_slots)
    for index, stack_data in enumerate(player_data.get("hotbar_slots", [])):
        if index < len(player.hotbar_slots):
            player.hotbar_slots[index] = deserialize_item_stack(stack_data)
    player.selected_hotbar_index = max(
        0,
        min(len(player.hotbar_slots) - 1, int(player_data.get("selected_hotbar_index", 0))),
    )
    player.active_effects = deserialize_active_effects(player_data.get("active_effects", []))
    player._sync_inventory_capacities()
    player.health = min(player_data.get("health", player.health), player.get_max_health())
    player.stamina = min(player_data.get("stamina", player.stamina), player.get_max_stamina())


@dataclass
class SaveSlotMeta:
    slot_id: str
    title: str
    created_at: str
    updated_at: str
    current_level: str | None = None
    player_level: int = 1
    last_checkpoint_name: str | None = None
    version: int = SAVE_VERSION

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SaveSlotMeta":
        return cls(
            slot_id=str(data.get("slot_id", "")),
            title=str(data.get("title", "")) or "Save",
            created_at=str(data.get("created_at", "")) or _utc_now_iso(),
            updated_at=str(data.get("updated_at", "")) or _utc_now_iso(),
            current_level=data.get("current_level"),
            player_level=max(1, int(data.get("player_level", 1))),
            last_checkpoint_name=data.get("last_checkpoint_name"),
            version=max(1, int(data.get("version", SAVE_VERSION))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_level": self.current_level,
            "player_level": self.player_level,
            "last_checkpoint_name": self.last_checkpoint_name,
            "version": self.version,
        }


class SaveManager:
    def __init__(self, root_path: Path | None = None):
        self.root_path = Path(root_path or get_save_root())
        self.index_path = self.root_path / INDEX_FILE_NAME
        self.active_slot_id: str | None = None

    def ensure_root(self) -> None:
        self.root_path.mkdir(parents=True, exist_ok=True)

    @property
    def app_settings_path(self) -> Path:
        return self.root_path / APP_SETTINGS_FILE_NAME

    def load_app_settings(self) -> dict[str, Any]:
        self.ensure_root()
        if not self.app_settings_path.exists():
            return {}
        try:
            raw_data = json.loads(self.app_settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return raw_data if isinstance(raw_data, dict) else {}

    def save_app_settings(self, settings_data: dict[str, Any]) -> bool:
        self.ensure_root()
        try:
            self.app_settings_path.write_text(
                json.dumps(settings_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True
        except OSError:
            return False

    def list_slots(self) -> list[SaveSlotMeta]:
        self.ensure_root()
        if not self.index_path.exists():
            return []
        try:
            raw_data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        slots = [SaveSlotMeta.from_dict(item) for item in raw_data.get("slots", []) if item.get("slot_id")]
        return sorted(slots, key=lambda slot: slot.updated_at, reverse=True)

    def has_slots(self) -> bool:
        return bool(self.list_slots())

    def get_slot_meta(self, slot_id: str) -> SaveSlotMeta | None:
        normalized_id = str(slot_id)
        for slot in self.list_slots():
            if slot.slot_id == normalized_id:
                return slot
        return None

    def create_slot(self, title: str) -> SaveSlotMeta:
        cleaned_title = str(title).strip() or f"Save {len(self.list_slots()) + 1}"
        timestamp = _utc_now_iso()
        slot = SaveSlotMeta(
            slot_id=uuid.uuid4().hex[:12],
            title=cleaned_title,
            created_at=timestamp,
            updated_at=timestamp,
        )
        slots = self.list_slots()
        slots.append(slot)
        self._write_index(slots)
        self.active_slot_id = slot.slot_id
        return slot

    def set_active_slot(self, slot_id: str | None) -> bool:
        if slot_id is None:
            self.active_slot_id = None
            return True
        slot = self.get_slot_meta(slot_id)
        if slot is None:
            return False
        self.active_slot_id = slot.slot_id
        return True

    def get_active_slot_meta(self) -> SaveSlotMeta | None:
        if self.active_slot_id is None:
            return None
        return self.get_slot_meta(self.active_slot_id)

    def get_slot_dir(self, slot_id: str) -> Path:
        return self.root_path / str(slot_id)

    def get_slot_save_path(self, slot_id: str) -> Path:
        return self.get_slot_dir(slot_id) / SAVE_FILE_NAME

    def load_slot_data(self, slot_id: str) -> dict[str, Any] | None:
        save_path = self.get_slot_save_path(slot_id)
        if not save_path.exists():
            return None
        try:
            data = json.loads(save_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if int(data.get("version", 0)) not in SUPPORTED_SAVE_VERSIONS:
            return None
        return data

    def save_slot(self, slot_id: str, snapshot: dict[str, Any], *, title: str | None = None) -> bool:
        slot = self.get_slot_meta(slot_id)
        if slot is None:
            return False

        self.ensure_root()
        slot_dir = self.get_slot_dir(slot_id)
        slot_dir.mkdir(parents=True, exist_ok=True)
        save_path = slot_dir / SAVE_FILE_NAME
        try:
            with open(save_path, "w", encoding="utf-8") as file_handle:
                json.dump(snapshot, file_handle, indent=2, ensure_ascii=False)
        except OSError:
            return False

        slot.updated_at = snapshot.get("saved_at", _utc_now_iso())
        if title is not None and str(title).strip():
            slot.title = str(title).strip()
        slot.current_level = snapshot.get("current_level")
        player_data = snapshot.get("player", {})
        slot.player_level = max(1, int(player_data.get("level", slot.player_level)))
        slot.last_checkpoint_name = snapshot.get("meta", {}).get("last_checkpoint_name")
        slot.version = int(snapshot.get("version", SAVE_VERSION))

        slots = self.list_slots()
        updated_slots = [slot if current.slot_id == slot.slot_id else current for current in slots]
        self._write_index(updated_slots)
        self.active_slot_id = slot.slot_id
        return True

    def delete_slot(self, slot_id: str) -> bool:
        slot = self.get_slot_meta(slot_id)
        if slot is None:
            return False

        slot_dir = self.get_slot_dir(slot_id)
        try:
            if slot_dir.exists():
                shutil.rmtree(slot_dir)
        except OSError:
            return False

        slots = [current for current in self.list_slots() if current.slot_id != str(slot_id)]
        self._write_index(slots)
        if self.active_slot_id == str(slot_id):
            self.active_slot_id = None
        return True

    def _write_index(self, slots: list[SaveSlotMeta]) -> None:
        self.ensure_root()
        payload = {
            "version": SAVE_VERSION,
            "slots": [slot.to_dict() for slot in slots],
        }
        self.index_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
