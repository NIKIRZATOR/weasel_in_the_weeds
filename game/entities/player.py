import math

import pygame

from game.core.assets import load_image
from game.core.timer import Timer
from game.core.vector import Vector2
from game.entities.entity import Entity
from settings import (
    ATTACK_COOLDOWN,
    ATTACK_COST,
    ATTACK_DURATION,
    COLOR_PLAYER,
    HEALTH_REGEN,
    HURT_DURATION,
    JUMP_DURATION,
    JUMP_HEIGHT,
    PLAYER_IDLE_SPRITE,
    PLAYER_HITBOX_HEIGHT,
    PLAYER_HITBOX_OFFSET_X,
    PLAYER_HITBOX_OFFSET_Y,
    PLAYER_HITBOX_WIDTH,
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

        self.health = PLAYER_MAX_HEALTH
        self.stamina = PLAYER_MAX_STAMINA

        self.is_running = False
        self.is_jumping = False
        self.is_attacking = False
        self.is_hurt = False

        self.direction = Vector2(1, 0)
        self.facing_left = False

        self.jump_timer = Timer(JUMP_DURATION)
        self.attack_timer = Timer(ATTACK_DURATION)
        self.attack_cooldown = Timer(ATTACK_COOLDOWN)
        self.hurt_timer = Timer(HURT_DURATION)

        self.jump_start_pos = Vector2()
        self.jump_end_pos = Vector2()
        self.jump_offset = 0
        self.jump_distance = self.width * 1.5

        self.current_speed = PLAYER_SPEED

    def update(self, dt, keys, world):
        if self.health <= 0:
            self.respawn()

        self.update_timers(dt)

        if not self.is_jumping and not self.is_hurt:
            self.handle_movement(dt, keys, world)

        if self.is_jumping:
            self.update_jump()

        self.handle_stamina(dt)
        self.handle_health_regen(dt)

    def update_timers(self, dt):
        if self.jump_timer.update(dt):
            self.complete_jump()

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
        self.current_speed = PLAYER_RUN_SPEED if self.is_running else PLAYER_SPEED

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

    def attack(self):
        if self.attack_cooldown.is_active():
            return False

        if self.stamina < ATTACK_COST:
            return False

        self.is_attacking = True
        self.attack_timer.start()
        self.attack_cooldown.start()
        self.stamina -= ATTACK_COST
        return True

    def take_damage(self, damage):
        self.health = max(0, self.health - damage)
        self.is_hurt = True
        self.hurt_timer.start()

    def handle_stamina(self, dt):
        if self.is_running:
            self.stamina = max(0, self.stamina - STAMINA_RUN_COST * dt)
        elif self.stamina < PLAYER_MAX_STAMINA:
            self.stamina = min(PLAYER_MAX_STAMINA, self.stamina + STAMINA_REGEN * dt)

    def handle_health_regen(self, dt):
        if 0 < self.health < PLAYER_MAX_HEALTH:
            self.health = min(PLAYER_MAX_HEALTH, self.health + HEALTH_REGEN * dt)

    def respawn(self):
        self.health = PLAYER_MAX_HEALTH
        self.stamina = PLAYER_MAX_STAMINA
        self.position = Vector2(self.spawn_position.x, self.spawn_position.y)
        self.is_running = False
        self.is_jumping = False
        self.is_attacking = False
        self.is_hurt = False
        self.jump_offset = 0
        self.jump_timer.active = False
        self.attack_timer.active = False
        self.attack_cooldown.active = False
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
        color = (255, 255, 255) if self.is_hurt else COLOR_PLAYER

        if self.sprite is None:
            pygame.draw.rect(
                screen,
                color,
                (screen_pos.x, screen_pos.y, self.width, self.height),
            )
            return

        sprite = self.sprite
        if self.facing_left:
            sprite = pygame.transform.flip(sprite, True, False)
        if self.is_hurt:
            sprite = sprite.copy()
            sprite.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_ADD)

        screen.blit(sprite, (screen_pos.x, screen_pos.y))

    def _draw_attack(self, screen, screen_pos):
        attack_offset = 40
        attack_height = 6

        center_x = screen_pos.x + self.width // 2
        center_y = screen_pos.y + self.height // 2

        if self.direction.x > 0:
            start_x = screen_pos.x + self.width
            start_y = center_y
            end_x = start_x + attack_offset
            end_y = start_y
        elif self.direction.x < 0:
            start_x = screen_pos.x
            start_y = center_y
            end_x = start_x - attack_offset
            end_y = start_y
        elif self.direction.y > 0:
            start_x = center_x
            start_y = screen_pos.y + self.height
            end_x = start_x
            end_y = start_y + attack_offset
        else:
            start_x = center_x
            start_y = screen_pos.y
            end_x = start_x
            end_y = start_y - attack_offset

        pygame.draw.line(
            screen,
            (255, 200, 0),
            (start_x, start_y),
            (end_x, end_y),
            attack_height,
        )
