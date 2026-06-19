import math

import pygame

from game.core.assets import load_image
from game.core.timer import Timer
from game.core.vector import Vector2
from game.entities.entity import Entity
from game.items import CharacterStats, Equipment, Inventory, ItemStack, create_item_stack
from game.items.types import EquipSlot, ItemKind
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


class Player(Entity):
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
        self.inventory = Inventory(PLAYER_INVENTORY_CAPACITY)
        self.equipment = Equipment()
        self.hotbar_slots: list[ItemStack | None] = [None] * HOTBAR_SIZE
        self.coins = 0
        self.selected_hotbar_index = 0
        self.story_flags = set()

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

        self.jump_start_pos = Vector2()
        self.jump_end_pos = Vector2()
        self.jump_offset = 0
        self.jump_distance = self.width * 1.5
        self.dash_direction = Vector2()
        self.dash_speed = DASH_DISTANCE / DASH_DURATION if DASH_DURATION > 0 else 0

        self.current_speed = self.get_effective_stats().speed

    def get_effective_stats(self):
        return self.base_stats + self.equipment.get_stat_bonuses()

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
        return self.inventory.can_add_item(item_or_stack, quantity)

    def add_item(self, item_or_stack, quantity=1):
        return self.inventory.add_item(item_or_stack, quantity)

    def remove_item(self, item_id, quantity=1):
        return self.inventory.remove_item(item_id, quantity)

    def has_item(self, item_id, quantity=1):
        return self.inventory.has_item(item_id, quantity)

    def find_item(self, item_id):
        return self.inventory.find_item(item_id)

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
                coins += item_stack.quantity
                item_stack = None
            elif not self.inventory.can_add_item(item_stack):
                return False

        if item_stack is not None and not self.inventory.add_item(item_stack):
            return False
        if coins > 0:
            self.add_coins(coins)
        self._sync_resource_limits()
        return True

    def update(self, dt, keys, world):
        if self.health <= 0:
            self.respawn()

        self.update_timers(dt)

        if self.is_dashing:
            self.update_dash(dt, world)
        elif not self.is_jumping and not self.is_hurt:
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

        self.attack_cooldown.update(dt)

        if self.hurt_timer.update(dt):
            self.is_hurt = False

    def handle_movement(self, dt, keys, world):
        movement = self._read_movement_input(keys)
        dx = movement.x
        dy = movement.y

        self.is_running = keys[pygame.K_LSHIFT] and self.stamina > 0 and (dx != 0 or dy != 0)
        self.current_speed = PLAYER_RUN_SPEED if self.is_running else self.get_speed()

        if dx == 0 and dy == 0:
            return

        step_speed = self.current_speed
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

    def attack_towards(self, target_x, target_y):
        if self.is_dashing or self.attack_cooldown.is_active():
            return False

        if self.stamina < ATTACK_COST:
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
        self.attack_timer.start()
        self.attack_cooldown.start()
        self.stamina -= ATTACK_COST
        return True

    def take_damage(self, damage):
        if self.is_dashing:
            return False

        mitigated = max(0, int(damage) - self.get_defense())
        if mitigated <= 0:
            return False
        self.health = max(0, self.health - mitigated)
        self.is_hurt = True
        self.hurt_timer.start()
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

    def set_respawn_point(self, spawn_x, spawn_y):
        self.spawn_position = Vector2(spawn_x, spawn_y)

    def move_to_spawn(self, spawn_x, spawn_y):
        self.spawn_position = Vector2(spawn_x, spawn_y)
        self.position = Vector2(spawn_x, spawn_y)
        self.is_running = False
        self.is_jumping = False
        self.is_dashing = False
        self.is_attacking = False
        self.is_hurt = False
        self.is_hidden = False
        self.jump_offset = 0
        self.jump_timer.active = False
        self.dash_timer.active = False
        self.dash_cooldown.active = False
        self.attack_timer.active = False
        self.hurt_timer.active = False

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
        attack_offset = 40
        attack_height = 6

        center_x = screen_pos.x + self.width // 2
        center_y = screen_pos.y + self.height // 2
        aim = self.aim_direction.normalize() if self.aim_direction.length() > 0 else Vector2(1, 0)
        start_x = center_x + aim.x * 12
        start_y = center_y + aim.y * 12
        end_x = start_x + aim.x * attack_offset
        end_y = start_y + aim.y * attack_offset

        pygame.draw.line(
            screen,
            (255, 200, 0),
            (start_x, start_y),
            (end_x, end_y),
            attack_height,
        )

    def _sync_resource_limits(self):
        self.health = min(self.health, self.get_max_health())
        self.stamina = min(self.stamina, self.get_max_stamina())
