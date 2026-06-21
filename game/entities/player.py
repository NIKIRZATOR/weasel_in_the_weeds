import math
from dataclasses import dataclass

import pygame

from game.core.assets import load_image
from game.core.timer import Timer
from game.core.vector import Vector2
from game.entities.entity import Entity
from game.items import CharacterStats, Equipment, Inventory, ItemStack, create_item_stack
from game.items.models import WeaponAttackProfile
from game.items.types import EquipSlot, ItemKind
from game.progression import build_progression_bonuses, get_skill_node_definition, get_xp_to_next_level
from settings import (
    ATTACK_COOLDOWN,
    ATTACK_COST,
    ATTACK_DURATION,
    COLOR_PLAYER,
    DASH_COOLDOWN,
    DASH_DISTANCE,
    DASH_DURATION,
    HEALTH_REGEN,
    HOTBAR_SIZE,
    HURT_DURATION,
    JUMP_DURATION,
    JUMP_HEIGHT,
    PLAYER_IDLE_SPRITE,
    PLAYER_HITBOX_HEIGHT,
    PLAYER_HITBOX_OFFSET_X,
    PLAYER_HITBOX_OFFSET_Y,
    PLAYER_HITBOX_WIDTH,
    PLAYER_INVENTORY_CAPACITY,
    PLAYER_INTERACTION_HEIGHT,
    PLAYER_INTERACTION_OFFSET_X,
    PLAYER_INTERACTION_OFFSET_Y,
    PLAYER_INTERACTION_WIDTH,
    PLAYER_MAX_HEALTH,
    PLAYER_MAX_STAMINA,
    PLAYER_RUN_SPEED,
    PLAYER_SIZE,
    PLAYER_SPEED,
    STAMINA_JUMP_COST,
    STAMINA_DASH_COST,
    STAMINA_REGEN,
    STAMINA_RUN_COST,
)


@dataclass
class AttackContext:
    kind: str
    damage: int
    range: float
    thickness: int
    shape: str
    arc_degrees: float
    duration: float
    cooldown: float
    recovery: float
    stamina_cost: float
    knockback: float
    stagger: float
    aim_direction: Vector2
    weapon_class: str | None = None
    is_ranged: bool = False
    projectile_speed: float = 320.0
    projectile_radius: int = 5
    projectile_distance: float = 520.0


DEFAULT_ATTACK_PROFILES = {
    "light": WeaponAttackProfile(
        damage_bonus=1,
        damage_multiplier=1.0,
        range=34,
        thickness=34,
        shape="arc",
        arc_degrees=42,
        duration=0.16,
        cooldown=0.18,
        stamina_cost=2.0,
        recovery=0.02,
        knockback=18.0,
        stagger=0.04,
    ),
    "heavy": WeaponAttackProfile(
        damage_bonus=2,
        damage_multiplier=1.3,
        range=42,
        thickness=42,
        shape="arc",
        arc_degrees=64,
        duration=0.24,
        cooldown=0.34,
        stamina_cost=7.0,
        recovery=0.12,
        knockback=34.0,
        stagger=0.12,
    ),
    "charged": WeaponAttackProfile(
        damage_bonus=4,
        damage_multiplier=1.8,
        range=54,
        thickness=48,
        shape="arc",
        arc_degrees=84,
        duration=0.34,
        cooldown=0.55,
        stamina_cost=14.0,
        recovery=0.22,
        knockback=52.0,
        stagger=0.22,
    ),
}


class Player(Entity):
    QUEST_INVENTORY_CAPACITY = 10
    """Класс игрока с состояниями, движением и базовой отрисовкой."""

    def __init__(self, x, y, spawn_x=None, spawn_y=None):
        super().__init__(
            x,
            y,
            PLAYER_SIZE,
            PLAYER_SIZE,
            hitbox_width=PLAYER_HITBOX_WIDTH,
            hitbox_height=PLAYER_HITBOX_HEIGHT,
            hitbox_offset_x=PLAYER_HITBOX_OFFSET_X,
            hitbox_offset_y=PLAYER_HITBOX_OFFSET_Y,
            interaction_width=PLAYER_INTERACTION_WIDTH,
            interaction_height=PLAYER_INTERACTION_HEIGHT,
            interaction_offset_x=PLAYER_INTERACTION_OFFSET_X,
            interaction_offset_y=PLAYER_INTERACTION_OFFSET_Y,
        )
        self.spawn_position = Vector2(
            x if spawn_x is None else spawn_x,
            y if spawn_y is None else spawn_y,
        )
        self.sprite = load_image(PLAYER_IDLE_SPRITE, (self.width, self.height))

        self.base_stats = CharacterStats(
            max_health=PLAYER_MAX_HEALTH,
            max_stamina=PLAYER_MAX_STAMINA,
            attack=0,
            defense=0,
            speed=PLAYER_SPEED,
        )
        self.base_inventory_capacity = PLAYER_INVENTORY_CAPACITY
        self.inventory = Inventory(PLAYER_INVENTORY_CAPACITY)
        self.quest_inventory = Inventory(self.QUEST_INVENTORY_CAPACITY)
        self.equipment = Equipment()
        self.hotbar_slots: list[ItemStack | None] = [None] * HOTBAR_SIZE
        self.coins = 0
        self.knowledge_shards = 0
        self.selected_hotbar_index = 0
        self.story_flags = set()
        self.unlocked_recipe_ids = set()
        self.explored_tiles_by_level: dict[str, list[list[bool]]] = {}
        self.claimed_dialogue_rewards_by_npc: dict[str, set[str]] = {}
        self.awarded_xp_sources = set()
        self.level = 1
        self.xp = 0
        self.skill_points = 0
        self.unlocked_skill_ids = set()

        self.health = self.get_max_health()
        self.stamina = self.get_max_stamina()

        self.is_running = False
        self.is_jumping = False
        self.is_dashing = False
        self.is_attacking = False
        self.is_hurt = False
        self.is_hidden = False

        self.direction = Vector2(1, 0)
        self.aim_direction = Vector2(1, 0)
        self.facing_left = False

        self.jump_timer = Timer(JUMP_DURATION)
        self.dash_timer = Timer(DASH_DURATION)
        self.dash_cooldown = Timer(DASH_COOLDOWN)
        self.attack_timer = Timer(ATTACK_DURATION)
        self.attack_cooldown = Timer(ATTACK_COOLDOWN)
        self.hurt_timer = Timer(HURT_DURATION)
        self.recovery_timer = Timer(0.0)

        self.jump_start_pos = Vector2()
        self.jump_end_pos = Vector2()
        self.jump_offset = 0
        self.jump_distance = self.width * 1.5
        self.dash_direction = Vector2()
        self.dash_speed = DASH_DISTANCE / DASH_DURATION if DASH_DURATION > 0 else 0

        self.current_speed = self.get_effective_stats().speed
        self.active_attack: AttackContext | None = None
        self.last_attack_fail_reason = ""
        self.knockback_velocity = Vector2()
        self.control_stun_timer = Timer(0.0)
        self._sync_inventory_capacities()

    def get_effective_stats(self):
        return self.base_stats + self.equipment.get_stat_bonuses() + self.get_progression_bonuses().stats

    def get_progression_bonuses(self):
        return build_progression_bonuses(self.unlocked_skill_ids)

    def get_max_health(self):
        return self.get_effective_stats().max_health

    def get_max_stamina(self):
        return self.get_effective_stats().max_stamina

    def get_attack(self):
        return self.get_effective_stats().attack

    def get_defense(self):
        return self.get_effective_stats().defense

    def get_speed(self):
        return self.get_effective_stats().speed

    def get_equipped_weapon(self):
        return self.equipment.get(EquipSlot.WEAPON)

    def get_xp_to_next_level(self):
        return get_xp_to_next_level(self.level)

    def get_attack_move_speed_multiplier(self):
        bonuses = self.get_progression_bonuses()
        return 1.0 + bonuses.attack_move_speed_multiplier_bonus

    def get_charge_time_multiplier(self):
        return self.get_progression_bonuses().charge_time_multiplier

    def get_attack_recovery_multiplier(self):
        return self.get_progression_bonuses().recovery_multiplier

    def has_unlocked_skill_node(self, node_id):
        return str(node_id) in self.unlocked_skill_ids

    def can_unlock_skill_node(self, node_id):
        node = get_skill_node_definition(node_id)
        if node is None or self.has_unlocked_skill_node(node_id) or self.skill_points <= 0:
            return False
        return all(self.has_unlocked_skill_node(required_id) for required_id in node.requires)

    def unlock_skill_node(self, node_id):
        if not self.can_unlock_skill_node(node_id):
            return False
        self.skill_points -= 1
        self.unlocked_skill_ids.add(str(node_id))
        self._sync_resource_limits()
        return True

    def add_experience(self, amount, source_key=None):
        amount = max(0, int(amount))
        if amount <= 0:
            return {"gained": 0, "level_ups": 0}
        if source_key is not None:
            source_key = str(source_key)
            if source_key in self.awarded_xp_sources:
                return {"gained": 0, "level_ups": 0}
            self.awarded_xp_sources.add(source_key)

        self.xp += amount
        level_ups = 0
        while self.xp >= self.get_xp_to_next_level():
            self.xp -= self.get_xp_to_next_level()
            self.level += 1
            self.skill_points += 1
            level_ups += 1
        self._sync_resource_limits()
        return {"gained": amount, "level_ups": level_ups}

    def get_attack_profile(self, attack_kind):
        attack_kind = str(attack_kind)
        weapon = self.get_equipped_weapon()
        if weapon is not None:
            profile = weapon.definition.get_attack_profile(attack_kind)
            if profile is not None:
                return profile
        if attack_kind == "charged":
            return None
        return DEFAULT_ATTACK_PROFILES.get(attack_kind, DEFAULT_ATTACK_PROFILES["light"])

    def get_current_attack_context(self):
        return self.active_attack

    def is_recovering(self):
        return self.recovery_timer.is_active()

    def get_hotbar_stack(self, index):
        if 0 <= index < HOTBAR_SIZE:
            return self.hotbar_slots[index]
        return None

    def get_hotbar_stacks(self):
        return [self.get_hotbar_stack(index) for index in range(HOTBAR_SIZE)]

    def select_hotbar_slot(self, index):
        if 0 <= index < HOTBAR_SIZE:
            self.selected_hotbar_index = index
            return True
        return False

    def clear_hotbar_slot(self, index):
        if not 0 <= index < HOTBAR_SIZE:
            return None
        stack = self.hotbar_slots[index]
        self.hotbar_slots[index] = None
        return stack

    def set_hotbar_slot(self, index, stack):
        if not 0 <= index < HOTBAR_SIZE:
            return False
        self.hotbar_slots[index] = stack
        return True

    def swap_hotbar_slots(self, first, second):
        if not (0 <= first < HOTBAR_SIZE and 0 <= second < HOTBAR_SIZE):
            return False
        self.hotbar_slots[first], self.hotbar_slots[second] = (
            self.hotbar_slots[second],
            self.hotbar_slots[first],
        )
        return True

    def swap_inventory_and_hotbar(self, inventory_index, hotbar_index):
        if not 0 <= hotbar_index < HOTBAR_SIZE:
            return False

        inventory_stack = self.inventory.get_stack_at(inventory_index)
        hotbar_stack = self.hotbar_slots[hotbar_index]
        if inventory_stack is None and hotbar_stack is None:
            return False

        if not self.inventory.set_stack_at(inventory_index, hotbar_stack):
            return False
        self.hotbar_slots[hotbar_index] = inventory_stack
        return True

    def can_add_item(self, item_or_stack, quantity=1):
        stack = self._resolve_item_stack(item_or_stack, quantity)
        if stack is None:
            return False
        return self._target_inventory_for_stack(stack).can_add_item(stack)

    def add_item(self, item_or_stack, quantity=1):
        stack = self._resolve_item_stack(item_or_stack, quantity)
        if stack is None:
            return False

        if not self._target_inventory_for_stack(stack).add_item(stack):
            return False
        self._sync_inventory_capacities()
        return True

    def remove_item(self, item_id, quantity=1):
        if quantity <= 0:
            return False
        if not self.has_item(item_id, quantity):
            return False

        remaining = quantity
        for inventory in self._inventories_for_item_id(item_id):
            available = inventory.count_item(item_id)
            if available <= 0:
                continue
            removed_now = min(remaining, available)
            if inventory.remove_item(item_id, removed_now):
                remaining -= removed_now
            if remaining <= 0:
                self._sync_inventory_capacities()
                return True

        self._sync_inventory_capacities()
        return False

    def has_item(self, item_id, quantity=1):
        return self.inventory.count_item(item_id) + self.quest_inventory.count_item(item_id) >= quantity

    def find_item(self, item_id):
        result = self.inventory.find_item(item_id)
        if result is not None:
            return result
        return self.quest_inventory.find_item(item_id)

    def add_coins(self, quantity):
        if quantity <= 0:
            return False
        self.coins += int(quantity)
        return True

    def can_spend_coins(self, quantity):
        return self.coins >= quantity

    def spend_coins(self, quantity):
        if quantity <= 0 or self.coins < quantity:
            return False
        self.coins -= int(quantity)
        return True

    def add_knowledge_shards(self, quantity):
        if quantity <= 0:
            return False
        self.knowledge_shards += int(quantity)
        return True

    def can_spend_knowledge_shards(self, quantity):
        return self.knowledge_shards >= quantity

    def spend_knowledge_shards(self, quantity):
        if quantity <= 0 or self.knowledge_shards < quantity:
            return False
        self.knowledge_shards -= int(quantity)
        return True

    def set_flag(self, flag):
        if not flag:
            return False
        self.story_flags.add(str(flag))
        return True

    def unset_flag(self, flag):
        if not flag:
            return False
        self.story_flags.discard(str(flag))
        return True

    def has_flag(self, flag):
        return str(flag) in self.story_flags

    def has_flags(self, flags):
        return all(self.has_flag(flag) for flag in flags)

    def can_open_map(self):
        return self.has_flag("has_map") or self.has_item("map")

    def ensure_map_state(self, level_key, width, height):
        existing = self.explored_tiles_by_level.get(level_key)
        if existing is not None and len(existing) == height and len(existing[0]) == width:
            return existing

        visited = [[False for _ in range(width)] for _ in range(height)]
        self.explored_tiles_by_level[level_key] = visited
        return visited

    def reveal_map_area(self, level_key, width, height, tile_x, tile_y, radius=1):
        visited = self.ensure_map_state(level_key, width, height)
        changed = False
        min_y = max(0, tile_y - radius)
        max_y = min(height - 1, tile_y + radius)
        min_x = max(0, tile_x - radius)
        max_x = min(width - 1, tile_x + radius)

        for row in range(min_y, max_y + 1):
            for col in range(min_x, max_x + 1):
                if visited[row][col]:
                    continue
                visited[row][col] = True
                changed = True
        return changed

    def get_map_state(self, level_key, width=None, height=None):
        visited = self.explored_tiles_by_level.get(level_key)
        if visited is None and width is not None and height is not None:
            visited = self.ensure_map_state(level_key, width, height)
        return visited

    def has_claimed_dialogue_reward(self, npc_key, node_id):
        if not npc_key or not node_id:
            return False
        return str(node_id) in self.claimed_dialogue_rewards_by_npc.get(str(npc_key), set())

    def mark_dialogue_reward_claimed(self, npc_key, node_id):
        if not npc_key or not node_id:
            return False
        claimed_nodes = self.claimed_dialogue_rewards_by_npc.setdefault(str(npc_key), set())
        claimed_nodes.add(str(node_id))
        return True

    def has_unlocked_recipe(self, recipe_id):
        return str(recipe_id) in self.unlocked_recipe_ids

    def unlock_recipe(self, recipe_id):
        if not recipe_id:
            return False
        self.unlocked_recipe_ids.add(str(recipe_id))
        return True

    def is_recipe_unlocked(self, recipe):
        if recipe is None:
            return False
        return recipe.is_default_unlocked() or self.has_unlocked_recipe(recipe.id)

    def can_unlock_recipe(self, recipe):
        if recipe is None or recipe.unlock_type != "knowledge":
            return False
        if self.is_recipe_unlocked(recipe):
            return False
        if recipe.required_flags and not self.has_flags(recipe.required_flags):
            return False
        return self.can_spend_knowledge_shards(recipe.knowledge_cost)

    def can_craft_recipe(self, recipe):
        if recipe is None or not self.is_recipe_unlocked(recipe):
            return False
        if recipe.required_flags and not self.has_flags(recipe.required_flags):
            return False
        for ingredient in recipe.ingredients:
            if not self.has_item(ingredient.item_id, ingredient.quantity):
                return False
        return self.can_add_item(recipe.result.item_id, recipe.result.quantity)

    def craft_recipe(self, recipe):
        if not self.can_craft_recipe(recipe):
            return False
        for ingredient in recipe.ingredients:
            if not self.remove_item(ingredient.item_id, ingredient.quantity):
                return False
        return self.add_item(recipe.result.item_id, recipe.result.quantity)

    def get_inventory_capacity(self):
        return self.base_inventory_capacity + self.get_inventory_capacity_bonus()

    def get_inventory_capacity_bonus(self):
        bonus = 0
        for inventory in (self.inventory, self.quest_inventory):
            for _, stack in inventory.iter_stacks():
                if stack is None:
                    continue
                bonus += max(0, int(stack.definition.inventory_capacity_bonus)) * stack.quantity
        return bonus

    def equip_inventory_slot(self, inventory_index, equip_slot):
        if not isinstance(equip_slot, EquipSlot):
            try:
                equip_slot = EquipSlot(equip_slot)
            except ValueError:
                return False

        stack = self.inventory.get_stack_at(inventory_index)
        if stack is None:
            return False
        if not self.equipment.can_equip_stack_to_slot(stack, equip_slot):
            return False

        removed = self.inventory.clear_slot(inventory_index)
        if removed is None:
            return False

        previous = self.equipment.get(equip_slot)
        if previous is not None:
            self.equipment.unequip_slot(equip_slot)
            if not self.inventory.add_item(previous):
                self.inventory.set_stack_at(inventory_index, removed)
                self.equipment.equip_stack_to_slot(previous, equip_slot)
                return False

        self.equipment.equip_stack_to_slot(removed, equip_slot)
        self._sync_resource_limits()
        return True

    def unequip_to_inventory(self, equip_slot):
        if not isinstance(equip_slot, EquipSlot):
            try:
                equip_slot = EquipSlot(equip_slot)
            except ValueError:
                return False

        stack = self.equipment.get(equip_slot)
        if stack is None:
            return False
        if not self.inventory.can_add_item(stack):
            return False

        removed = self.equipment.unequip_slot(equip_slot)
        if removed is None:
            return False
        if not self.inventory.add_item(removed):
            self.equipment.equip_stack_to_slot(removed, equip_slot)
            return False

        self._sync_resource_limits()
        return True

    def pickup_item(self, item_stack=None, coins=0):
        if item_stack is not None:
            if item_stack.kind == ItemKind.CURRENCY:
                if not self._add_currency_from_stack(item_stack):
                    return False
                item_stack = None
            elif not self._target_inventory_for_stack(item_stack).can_add_item(item_stack):
                return False

        if item_stack is not None and not self._target_inventory_for_stack(item_stack).add_item(item_stack):
            return False
        if coins > 0:
            self.add_coins(coins)
        self._sync_inventory_capacities()
        return True

    def _add_currency_from_stack(self, item_stack):
        wallet_key = item_stack.definition.wallet_key
        if wallet_key == "coins":
            return self.add_coins(item_stack.quantity)
        if wallet_key == "knowledge_shards":
            return self.add_knowledge_shards(item_stack.quantity)
        return False

    def _resolve_item_stack(self, item_or_stack, quantity=1):
        if isinstance(item_or_stack, ItemStack):
            return item_or_stack.copy(quantity if quantity != 1 else item_or_stack.quantity)
        return create_item_stack(item_or_stack, quantity)

    def _target_inventory_for_stack(self, stack):
        if stack.kind == ItemKind.QUEST:
            return self.quest_inventory
        return self.inventory

    def _inventories_for_item_id(self, item_id):
        in_regular = self.inventory.count_item(item_id) > 0
        in_quest = self.quest_inventory.count_item(item_id) > 0
        if in_regular and not in_quest:
            return [self.inventory]
        if in_quest and not in_regular:
            return [self.quest_inventory]
        return [self.inventory, self.quest_inventory]

    def _sync_inventory_capacities(self):
        self._normalize_quest_items()
        self.inventory.set_capacity(self.get_inventory_capacity())
        self._sync_resource_limits()

    def _normalize_quest_items(self):
        for index, stack in list(self.inventory.iter_stacks()):
            if stack is None or stack.kind != ItemKind.QUEST:
                continue
            if not self.quest_inventory.can_add_item(stack):
                continue
            self.quest_inventory.add_item(stack)
            self.inventory.clear_slot(index)

        for index, stack in enumerate(self.hotbar_slots):
            if stack is None or stack.kind != ItemKind.QUEST:
                continue
            if not self.quest_inventory.can_add_item(stack):
                continue
            self.quest_inventory.add_item(stack)
            self.hotbar_slots[index] = None

    def update(self, dt, keys, world):
        if self.health <= 0:
            self.respawn()

        self.update_timers(dt)

        if self._update_knockback(dt, world):
            pass
        elif self.is_dashing:
            self.update_dash(dt, world)
        elif (
            not self.is_jumping
            and not self.is_hurt
            and not self.control_stun_timer.is_active()
            and (self.is_attacking or not self.is_recovering())
        ):
            self.handle_movement(dt, keys, world)

        if self.is_jumping:
            self.update_jump()

        self.handle_stamina(dt)
        self.handle_health_regen(dt)
        self._sync_resource_limits()

    def update_timers(self, dt):
        if self.jump_timer.update(dt):
            self.complete_jump()

        if self.dash_timer.update(dt):
            self.complete_dash()

        self.dash_cooldown.update(dt)

        if self.attack_timer.update(dt):
            self.is_attacking = False
            self.active_attack = None

        self.attack_cooldown.update(dt)

        if self.hurt_timer.update(dt):
            self.is_hurt = False

        self.control_stun_timer.update(dt)
        self.recovery_timer.update(dt)

    def handle_movement(self, dt, keys, world):
        movement = self._read_movement_input(keys)
        dx = movement.x
        dy = movement.y

        self.is_running = keys[pygame.K_LSHIFT] and self.stamina > 0 and (dx != 0 or dy != 0)
        self.current_speed = PLAYER_RUN_SPEED if self.is_running else self.get_speed()

        if dx == 0 and dy == 0:
            return

        step_speed = self.current_speed
        if self.is_attacking:
            step_speed *= 0.5 * self.get_attack_move_speed_multiplier()
        if dx != 0 and dy != 0:
            step_speed *= 0.707

        new_position = Vector2(
            self.position.x + dx * step_speed * dt,
            self.position.y + dy * step_speed * dt,
        )

        if not world.check_collision(new_position.x, self.position.y, self):
            self.position.x = new_position.x
        if not world.check_collision(self.position.x, new_position.y, self):
            self.position.y = new_position.y

    def try_jump(self, direction, world):
        if self.is_jumping or self.stamina < STAMINA_JUMP_COST:
            return False

        if direction.length() == 0:
            return False

        direction_normalized = direction.normalize()
        new_position = Vector2(
            self.position.x + direction_normalized.x * self.jump_distance,
            self.position.y + direction_normalized.y * self.jump_distance,
        )

        if world.check_collision(new_position.x, new_position.y, self, ignore_jump=True):
            return False

        self.start_jump(new_position)
        self.stamina -= STAMINA_JUMP_COST
        return True

    def start_jump(self, target_position):
        self.is_jumping = True
        self.jump_timer.start()
        self.jump_start_pos = Vector2(self.position.x, self.position.y)
        self.jump_end_pos = target_position

    def try_dash(self, direction):
        if self.is_dashing or self.is_jumping or self.dash_cooldown.is_active():
            return False

        if self.stamina < STAMINA_DASH_COST:
            return False

        if direction.length() == 0:
            direction = self.direction
        if direction.length() == 0:
            return False

        self.dash_direction = direction.normalize()
        self.is_dashing = True
        self.is_running = False
        self.is_hurt = False
        self.dash_timer.start()
        self.dash_cooldown.start()
        self.stamina -= STAMINA_DASH_COST

        if self.dash_direction.x != 0:
            self.facing_left = self.dash_direction.x < 0
        return True

    def update_dash(self, dt, world):
        step = self.dash_direction * (self.dash_speed * dt)
        if not world.check_collision(self.position.x + step.x, self.position.y, self):
            self.position.x += step.x
        if not world.check_collision(self.position.x, self.position.y + step.y, self):
            self.position.y += step.y

    def complete_dash(self):
        self.is_dashing = False
        self.dash_direction = Vector2()

    def update_jump(self):
        progress = 1 - (self.jump_timer.current / self.jump_timer.duration)
        self.position.x = self.jump_start_pos.x + (self.jump_end_pos.x - self.jump_start_pos.x) * progress
        self.position.y = self.jump_start_pos.y + (self.jump_end_pos.y - self.jump_start_pos.y) * progress

        parabola = math.sin(progress * math.pi) * JUMP_HEIGHT
        self.jump_offset = -parabola

    def complete_jump(self):
        self.position = Vector2(self.jump_end_pos.x, self.jump_end_pos.y)
        self.is_jumping = False
        self.jump_offset = 0

    def attack_towards(self, target_x, target_y, attack_kind="light"):
        if self.is_dashing or self.attack_cooldown.is_active():
            self.last_attack_fail_reason = "busy"
            return False

        profile = self.get_attack_profile(attack_kind)
        if profile is None:
            self.last_attack_fail_reason = "no_attack_profile"
            return False
        progression_bonuses = self.get_progression_bonuses()
        stamina_cost = profile.stamina_cost
        if attack_kind == "light":
            stamina_cost *= progression_bonuses.light_stamina_cost_multiplier
        elif attack_kind == "heavy":
            stamina_cost *= progression_bonuses.heavy_stamina_cost_multiplier
        elif attack_kind == "charged":
            stamina_cost *= progression_bonuses.charged_stamina_cost_multiplier
        if self.stamina < stamina_cost:
            self.last_attack_fail_reason = "not_enough_stamina"
            return False

        center = self.get_center()
        aim = Vector2(target_x - center.x, target_y - center.y)
        if aim.length() == 0:
            aim = Vector2(1 if not self.facing_left else -1, 0)
        else:
            aim = aim.normalize()

        self.aim_direction = aim
        if aim.x != 0:
            self.facing_left = aim.x < 0

        self.is_attacking = True
        damage = max(1, int((self.get_attack() + profile.damage_bonus) * profile.damage_multiplier))
        if profile.is_ranged:
            damage += progression_bonuses.bow_damage_bonus
        if attack_kind == "charged":
            damage += progression_bonuses.charged_damage_bonus
        recovery = profile.recovery * self.get_attack_recovery_multiplier()
        self.active_attack = AttackContext(
            kind=str(attack_kind),
            damage=damage,
            range=profile.range,
            thickness=profile.thickness,
            shape=profile.shape,
            arc_degrees=profile.arc_degrees,
            duration=profile.duration,
            cooldown=profile.cooldown,
            recovery=recovery,
            stamina_cost=stamina_cost,
            knockback=profile.knockback,
            stagger=profile.stagger,
            aim_direction=aim,
            weapon_class=self.get_equipped_weapon().definition.weapon_class if self.get_equipped_weapon() is not None else None,
            is_ranged=profile.is_ranged,
            projectile_speed=profile.projectile_speed,
            projectile_radius=profile.projectile_radius,
            projectile_distance=profile.projectile_distance,
        )
        self.attack_timer.start(profile.duration)
        self.attack_cooldown.start(profile.cooldown)
        self.recovery_timer.start(profile.duration + recovery)
        self.stamina -= stamina_cost
        self.last_attack_fail_reason = ""
        return True

    def take_damage(self, damage, direction=None, force=0.0, stun_duration=None):
        if self.is_dashing:
            return False

        mitigated = max(0, int(damage) - self.get_defense())
        if mitigated <= 0:
            return False
        self.health = max(0, self.health - mitigated)
        self.is_hurt = True
        stun_time = HURT_DURATION if stun_duration is None else max(HURT_DURATION, float(stun_duration))
        self.hurt_timer.start(stun_time)
        if stun_duration is not None:
            self.control_stun_timer.start(float(stun_duration))
        if direction is not None and getattr(direction, "length", None) is not None and direction.length() > 0 and force > 0:
            self.knockback_velocity = direction.normalize() * float(force)
        return True

    def _update_knockback(self, dt, world):
        speed = self.knockback_velocity.length()
        if speed <= 0.01:
            self.knockback_velocity = Vector2()
            return False

        step = self.knockback_velocity * dt
        moved = False
        if not world.check_collision(self.position.x + step.x, self.position.y, self):
            self.position.x += step.x
            moved = True
        if not world.check_collision(self.position.x, self.position.y + step.y, self):
            self.position.y += step.y
            moved = True

        damping = max(0.0, 1.0 - dt * 8.0)
        self.knockback_velocity = self.knockback_velocity * damping
        if not moved:
            self.knockback_velocity = Vector2()
        return True

    def handle_stamina(self, dt):
        max_stamina = self.get_max_stamina()
        if self.is_running:
            self.stamina = max(0, self.stamina - STAMINA_RUN_COST * dt)
        elif self.stamina < max_stamina:
            self.stamina = min(max_stamina, self.stamina + STAMINA_REGEN * dt)

    def handle_health_regen(self, dt):
        max_health = self.get_max_health()
        if 0 < self.health < max_health:
            self.health = min(max_health, self.health + HEALTH_REGEN * dt)

    def respawn(self):
        self.health = self.get_max_health()
        self.stamina = self.get_max_stamina()
        self.position = Vector2(self.spawn_position.x, self.spawn_position.y)
        self.is_running = False
        self.is_jumping = False
        self.is_dashing = False
        self.is_attacking = False
        self.active_attack = None
        self.is_hurt = False
        self.is_hidden = False
        self.aim_direction = Vector2(1, 0)
        self.jump_offset = 0
        self.jump_timer.active = False
        self.dash_timer.active = False
        self.dash_cooldown.active = False
        self.attack_timer.active = False
        self.attack_cooldown.active = False
        self.hurt_timer.active = False
        self.control_stun_timer.active = False
        self.recovery_timer.active = False
        self.last_attack_fail_reason = ""
        self.knockback_velocity = Vector2()

    def set_respawn_point(self, spawn_x, spawn_y):
        self.spawn_position = Vector2(spawn_x, spawn_y)

    def move_to_spawn(self, spawn_x, spawn_y):
        self.spawn_position = Vector2(spawn_x, spawn_y)
        self.position = Vector2(spawn_x, spawn_y)
        self.is_running = False
        self.is_jumping = False
        self.is_dashing = False
        self.is_attacking = False
        self.active_attack = None
        self.is_hurt = False
        self.is_hidden = False
        self.jump_offset = 0
        self.jump_timer.active = False
        self.dash_timer.active = False
        self.dash_cooldown.active = False
        self.attack_timer.active = False
        self.hurt_timer.active = False
        self.control_stun_timer.active = False
        self.recovery_timer.active = False
        self.last_attack_fail_reason = ""
        self.knockback_velocity = Vector2()

    def get_visual_position(self):
        return Vector2(
            self.position.x,
            self.position.y + self.jump_offset,
        )

    def get_visual_center(self):
        visual_pos = self.get_visual_position()
        return Vector2(
            visual_pos.x + self.width / 2,
            visual_pos.y + self.height / 2,
        )

    def draw(self, screen, camera):
        visual_pos = self.get_visual_position()
        screen_pos = Vector2(
            visual_pos.x - camera.position.x,
            visual_pos.y - camera.position.y,
        )

        self._draw_body(screen, screen_pos)
        self._draw_weapon_marker(screen, screen_pos)

        if self.is_attacking:
            self._draw_attack(screen, screen_pos)

        self.draw_debug(screen, camera)

    def _read_movement_input(self, keys):
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1

        if dx != 0:
            self.direction = Vector2(dx, 0)
            self.facing_left = dx < 0
        elif dy != 0:
            self.direction = Vector2(0, dy)

        return Vector2(dx, dy)

    def _draw_body(self, screen, screen_pos):
        color = (180, 220, 255) if self.is_dashing else (255, 255, 255) if self.is_hurt else COLOR_PLAYER

        if self.sprite is None:
            body_color = (160, 160, 160) if self.is_hidden else color
            pygame.draw.rect(screen, body_color, (screen_pos.x, screen_pos.y, self.width, self.height))
            return

        sprite = self.sprite
        if self.facing_left:
            sprite = pygame.transform.flip(sprite, True, False)
        if self.is_hidden:
            sprite = sprite.copy()
            sprite.fill((90, 90, 90, 0), special_flags=pygame.BLEND_RGB_SUB)
            sprite.fill((35, 35, 35, 0), special_flags=pygame.BLEND_RGB_ADD)
        if self.is_dashing:
            sprite = sprite.copy()
            sprite.fill((40, 90, 140, 0), special_flags=pygame.BLEND_RGB_ADD)
        if self.is_hurt:
            sprite = sprite.copy()
            sprite.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_ADD)

        screen.blit(sprite, (screen_pos.x, screen_pos.y))

    def _draw_attack(self, screen, screen_pos):
        center_x = screen_pos.x + self.width // 2
        center_y = screen_pos.y + self.height // 2
        active_attack = self.get_current_attack_context()
        if active_attack is None:
            return
        attack_range = active_attack.range
        attack_height = max(4, int(active_attack.thickness * 0.2))
        aim = self.aim_direction.normalize() if self.aim_direction.length() > 0 else Vector2(1, 0)
        start_x = center_x + aim.x * 12
        start_y = center_y + aim.y * 12
        end_x = start_x + aim.x * attack_range
        end_y = start_y + aim.y * attack_range
        color = (140, 210, 255) if active_attack.is_ranged else (255, 200, 0)

        if active_attack.shape == "arc":
            perp = Vector2(-aim.y, aim.x)
            left = Vector2(end_x, end_y) + perp * (active_attack.thickness * 0.35)
            right = Vector2(end_x, end_y) - perp * (active_attack.thickness * 0.35)
            pygame.draw.polygon(screen, color, [(start_x, start_y), (left.x, left.y), (right.x, right.y)])
            return

        pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), attack_height)

    def _draw_weapon_marker(self, screen, screen_pos):
        weapon = self.get_equipped_weapon()
        if weapon is None:
            return

        weapon_class = weapon.definition.weapon_class or "blade"
        aim = self.aim_direction.normalize() if self.aim_direction.length() > 0 else Vector2(-1 if self.facing_left else 1, 0)
        hand_x = screen_pos.x + self.width * (0.34 if self.facing_left else 0.66)
        hand_y = screen_pos.y + self.height * 0.58

        if weapon_class == "dagger":
            tip_x = hand_x + aim.x * 18
            tip_y = hand_y + aim.y * 18
            pygame.draw.line(screen, (215, 215, 225), (hand_x, hand_y), (tip_x, tip_y), 4)
            pygame.draw.circle(screen, (120, 90, 60), (int(hand_x), int(hand_y)), 3)
            return

        if weapon_class == "spear":
            butt_x = hand_x - aim.x * 10
            butt_y = hand_y - aim.y * 10
            tip_x = hand_x + aim.x * 30
            tip_y = hand_y + aim.y * 30
            pygame.draw.line(screen, (140, 98, 58), (butt_x, butt_y), (tip_x, tip_y), 3)
            head_left = Vector2(tip_x, tip_y) + Vector2(-aim.y, aim.x) * 4
            head_right = Vector2(tip_x, tip_y) + Vector2(aim.y, -aim.x) * 4
            head_tip = Vector2(tip_x, tip_y) + aim * 8
            pygame.draw.polygon(
                screen,
                (210, 210, 220),
                [(head_left.x, head_left.y), (head_right.x, head_right.y), (head_tip.x, head_tip.y)],
            )
            return

        if weapon_class == "bow":
            perp = Vector2(-aim.y, aim.x)
            top = Vector2(hand_x, hand_y) + perp * 12
            bottom = Vector2(hand_x, hand_y) - perp * 12
            mid = Vector2(hand_x, hand_y) + aim * 8
            pygame.draw.line(screen, (122, 85, 52), (top.x, top.y), (mid.x, mid.y), 3)
            pygame.draw.line(screen, (122, 85, 52), (mid.x, mid.y), (bottom.x, bottom.y), 3)
            pygame.draw.line(screen, (220, 220, 235), (top.x, top.y), (bottom.x, bottom.y), 1)
            return

        tip_x = hand_x + aim.x * 22
        tip_y = hand_y + aim.y * 22
        pygame.draw.line(screen, (215, 215, 225), (hand_x, hand_y), (tip_x, tip_y), 4)
        pygame.draw.circle(screen, (120, 90, 60), (int(hand_x), int(hand_y)), 3)

    def _sync_resource_limits(self):
        self.health = min(self.health, self.get_max_health())
        self.stamina = min(self.stamina, self.get_max_stamina())
