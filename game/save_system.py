"""Система сохранения и загрузки прогресса игрока."""
import json
from pathlib import Path
from typing import Any

from game.items import create_item_stack
from game.items.models import ItemStack


SAVE_FILE_NAME = "savegame.json"


def get_save_path() -> Path:
    """Возвращает путь к файлу сохранения."""
    return Path.home() / ".weasel_in_the_weeds" / SAVE_FILE_NAME


def serialize_item_stack(stack: ItemStack | None) -> dict[str, Any] | None:
    """Сериализует ItemStack в словарь."""
    if stack is None:
        return None
    return {
        "item_id": stack.item_id,
        "quantity": stack.quantity,
    }


def deserialize_item_stack(data: dict[str, Any] | None) -> ItemStack | None:
    """Десериализует словарь в ItemStack."""
    if data is None:
        return None
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)
    if not item_id:
        return None
    return create_item_stack(item_id, quantity)


def serialize_inventory(inventory) -> list[dict[str, Any] | None]:
    """Сериализует инвентарь в список слотов."""
    return [serialize_item_stack(stack) for stack in inventory.slots]


def deserialize_inventory(inventory, data: list[dict[str, Any] | None]) -> None:
    """Десериализует список слотов в инвентарь."""
    for index, slot_data in enumerate(data):
        if index >= inventory.capacity:
            break
        inventory.slots[index] = deserialize_item_stack(slot_data)


def serialize_equipment(equipment) -> dict[str, dict[str, Any] | None]:
    """Сериализует экипировку в словарь слотов."""
    result = {}
    for slot, stack in equipment.slots.items():
        result[slot.value] = serialize_item_stack(stack)
    return result


def deserialize_equipment(equipment, data: dict[str, dict[str, Any] | None]) -> None:
    """Десериализует словарь слотов в экипировку."""
    from game.items.types import EquipSlot
    
    for slot_value, stack_data in data.items():
        try:
            slot = EquipSlot(slot_value)
        except ValueError:
            continue
        equipment.slots[slot] = deserialize_item_stack(stack_data)


def save_game(player, level_key: str, enemies: list | None = None) -> bool:
    """
    Сохраняет состояние игры в файл.
    
    Args:
        player: Объект игрока
        level_key: Ключ текущего уровня
        enemies: Список врагов на уровне (опционально)
    
    Returns:
        True если сохранение успешно, False иначе
    """
    try:
        save_path = get_save_path()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        save_data = {
            "version": 1,
            "level_key": level_key,
            "player": {
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
                "unlocked_skill_ids": list(player.unlocked_skill_ids),
                "story_flags": list(player.story_flags),
                "unlocked_recipe_ids": list(player.unlocked_recipe_ids),
                "awarded_xp_sources": list(player.awarded_xp_sources),
                "explored_tiles_by_level": {
                    level: [
                        [bool(cell) for cell in row]
                        for row in tiles
                    ]
                    for level, tiles in player.explored_tiles_by_level.items()
                },
                "container_states": player.container_states,
                "claimed_dialogue_rewards_by_npc": {
                    npc: list(nodes)
                    for npc, nodes in player.claimed_dialogue_rewards_by_npc.items()
                },
                "inventory": serialize_inventory(player.inventory),
                "quest_inventory": serialize_inventory(player.quest_inventory),
                "equipment": serialize_equipment(player.equipment),
                "hotbar_slots": [serialize_item_stack(stack) for stack in player.hotbar_slots],
            },
        }
        
        # Сохраняем состояние врагов, если переданы
        if enemies is not None:
            save_data["enemies"] = [
                {
                    "position": {
                        "x": enemy.position.x,
                        "y": enemy.position.y,
                    },
                    "health": enemy.health,
                    "is_dead": enemy.is_dead,
                }
                for enemy in enemies
                if not enemy.is_dead
            ]
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False


def load_game(player, level_key: str) -> dict[str, Any] | None:
    """
    Загружает состояние игры из файла.
    
    Args:
        player: Объект игрока для загрузки данных
        level_key: Ключ текущего уровня
    
    Returns:
        Словарь с дополнительными данными (враги и т.д.) или None при ошибке
    """
    try:
        save_path = get_save_path()
        if not save_path.exists():
            return None
        
        with open(save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        
        # Проверяем версию сохранения
        if save_data.get("version") != 1:
            print("Несовместимая версия сохранения")
            return None
        
        # Проверяем уровень
        if save_data.get("level_key") != level_key:
            print("Сохранение для другого уровня")
            return None
        
        player_data = save_data.get("player", {})
        
        # Загружаем позицию
        position = player_data.get("position", {})
        player.position.x = position.get("x", player.position.x)
        player.position.y = position.get("y", player.position.y)
        
        spawn_position = player_data.get("spawn_position", {})
        player.spawn_position.x = spawn_position.get("x", player.spawn_position.x)
        player.spawn_position.y = spawn_position.get("y", player.spawn_position.y)
        
        # Загружаем ресурсы
        player.health = player_data.get("health", player.health)
        player.stamina = player_data.get("stamina", player.stamina)
        player.level = player_data.get("level", player.level)
        player.xp = player_data.get("xp", player.xp)
        player.skill_points = player_data.get("skill_points", player.skill_points)
        player.coins = player_data.get("coins", player.coins)
        player.knowledge_shards = player_data.get("knowledge_shards", player.knowledge_shards)
        
        # Загружаем наборы ID
        player.unlocked_skill_ids = set(player_data.get("unlocked_skill_ids", []))
        player.story_flags = set(player_data.get("story_flags", []))
        player.unlocked_recipe_ids = set(player_data.get("unlocked_recipe_ids", []))
        player.awarded_xp_sources = set(player_data.get("awarded_xp_sources", []))
        
        # Загружаем исследованные тайлы
        explored_tiles = player_data.get("explored_tiles_by_level", {})
        player.explored_tiles_by_level = {
            level: [[bool(cell) for cell in row] for row in tiles]
            for level, tiles in explored_tiles.items()
        }
        
        # Загружаем состояния контейнеров
        player.container_states = player_data.get("container_states", {})
        
        # Загружаем полученные награды диалогов
        claimed_rewards = player_data.get("claimed_dialogue_rewards_by_npc", {})
        player.claimed_dialogue_rewards_by_npc = {
            npc: set(nodes)
            for npc, nodes in claimed_rewards.items()
        }
        
        # Загружаем инвентарь
        inventory_data = player_data.get("inventory", [])
        deserialize_inventory(player.inventory, inventory_data)
        
        quest_inventory_data = player_data.get("quest_inventory", [])
        deserialize_inventory(player.quest_inventory, quest_inventory_data)
        
        # Загружаем экипировку
        equipment_data = player_data.get("equipment", {})
        deserialize_equipment(player.equipment, equipment_data)
        
        # Загружаем хотбар
        hotbar_data = player_data.get("hotbar_slots", [])
        for index, stack_data in enumerate(hotbar_data):
            if index < len(player.hotbar_slots):
                player.hotbar_slots[index] = deserialize_item_stack(stack_data)
        
        # Синхронизируем емкости инвентаря
        player._sync_inventory_capacities()
        
        # Возвращаем дополнительные данные (враги и т.д.)
        return {
            "enemies": save_data.get("enemies", []),
        }
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return None


def has_save_file(level_key: str) -> bool:
    """Проверяет наличие файла сохранения для указанного уровня."""
    try:
        save_path = get_save_path()
        if not save_path.exists():
            return False
        
        with open(save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        
        return save_data.get("level_key") == level_key
    except Exception:
        return False
