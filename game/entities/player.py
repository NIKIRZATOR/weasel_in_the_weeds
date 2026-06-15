import math
import pygame
from game.entities.entity import Entity
from game.core.timer import Timer
from game.core.vector import Vector2
from settings import *

class Player(Entity):
    """Класс игрока с анимациями и состояниями"""
    
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_SIZE, PLAYER_SIZE)
        
        # Характеристики
        self.health = PLAYER_MAX_HEALTH
        self.stamina = PLAYER_MAX_STAMINA
        
        # Состояния
        self.is_running = False
        self.is_jumping = False
        self.is_attacking = False
        self.is_hurt = False
        
        # Направление игрока (для анимации атаки)
        self.direction = Vector2(1, 0)  # По умолчанию смотрим вправо
        
        # Таймеры
        self.jump_timer = Timer(JUMP_DURATION)
        self.attack_timer = Timer(ATTACK_DURATION)
        self.attack_cooldown = Timer(ATTACK_COOLDOWN)
        self.hurt_timer = Timer(HURT_DURATION)
        
        # Данные прыжка
        self.jump_start_pos = Vector2()
        self.jump_end_pos = Vector2()
        self.jump_offset = 0
        
        # Скорость
        self.current_speed = PLAYER_SPEED
    
    def update(self, dt, keys, world):
        if self.health <= 0:
            self.respawn()
        
        # Обновляем таймеры
        self.update_timers(dt)
        
        if not self.is_jumping and not self.is_hurt:
            self.handle_movement(dt, keys, world)
        
        if self.is_jumping:
            self.update_jump(dt)
        
        self.handle_stamina(dt)
        self.handle_health_regen(dt)
    
    def update_timers(self, dt):
        if self.jump_timer.update(dt):
            self.complete_jump()
        
        if self.attack_timer.update(dt):
            self.is_attacking = False
        
        # Обновляем кулдаун атаки
        if self.attack_cooldown.update(dt):
            pass  # Кулдаун закончился, можно снова атаковать
        
        if self.hurt_timer.update(dt):
            self.is_hurt = False
    
    def handle_movement(self, dt, keys, world):
        """Обработка движения с проверкой коллизий"""
        # Получаем направление
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
            dx = -1
            self.direction = Vector2(-1, 0)  # Смотрим влево
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: 
            dx = 1
            self.direction = Vector2(1, 0)   # Смотрим вправо
        if keys[pygame.K_UP] or keys[pygame.K_w]: 
            dy = -1
            self.direction = Vector2(0, -1)  # Смотрим вверх
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: 
            dy = 1
            self.direction = Vector2(0, 1)   # Смотрим вниз
        
        # Если двигаемся по диагонали, направление приоритетнее по горизонтали
        if dx != 0 or dy != 0:
            if dx != 0 and dy != 0:
                # При диагональном движении сохраняем последнее направление
                # (уже установлено выше)
                pass
        
        # Бег
        self.is_running = keys[pygame.K_LSHIFT] and self.stamina > 0 and (dx != 0 or dy != 0)
        self.current_speed = PLAYER_RUN_SPEED if self.is_running else PLAYER_SPEED
        
        # Движение
        if dx != 0 or dy != 0:
            if dx != 0 and dy != 0:
                self.current_speed *= 0.707
            
            new_position = Vector2(
                self.position.x + dx * self.current_speed * dt,
                self.position.y + dy * self.current_speed * dt
            )
            
            # Проверяем коллизии по отдельным осям
            if not world.check_collision(new_position.x, self.position.y, self):
                self.position.x = new_position.x
            if not world.check_collision(self.position.x, new_position.y, self):
                self.position.y = new_position.y
    
    def try_jump(self, direction, world):
        """Попытка прыжка через препятствие"""
        if self.is_jumping or self.stamina < STAMINA_JUMP_COST:
            return False
        
        if direction.length() == 0:
            return False
        
        dir_norm = direction.normalize()
        jump_distance = TILE_SIZE * 1.5
        
        new_position = Vector2(
            self.position.x + dir_norm.x * jump_distance,
            self.position.y + dir_norm.y * jump_distance
        )
        
        # Проверяем, можно ли прыгнуть
        if not world.check_collision(new_position.x, new_position.y, self, ignore_jump=True):
            self.start_jump(new_position)
            self.stamina -= STAMINA_JUMP_COST
            return True
        
        return False
    
    def start_jump(self, target_position):
        """Начинаем прыжок"""
        self.is_jumping = True
        self.jump_timer.start()
        self.jump_start_pos = Vector2(self.position.x, self.position.y)
        self.jump_end_pos = target_position
    
    def update_jump(self, dt):
        """Обновляем позицию во время прыжка (плавное движение)"""
        # Получаем прогресс прыжка (0 - начало, 1 - конец)
        progress = 1 - (self.jump_timer.current / self.jump_timer.duration)
        
        # Интерполяция позиции
        t = progress
        self.position.x = self.jump_start_pos.x + (self.jump_end_pos.x - self.jump_start_pos.x) * t
        self.position.y = self.jump_start_pos.y + (self.jump_end_pos.y - self.jump_start_pos.y) * t
        
        # Визуальный эффект параболы (смещение вверх-вниз)
        parabola = math.sin(t * math.pi) * JUMP_HEIGHT
        self.jump_offset = -parabola
    
    def complete_jump(self):
        """Завершение прыжка"""
        self.position = self.jump_end_pos
        self.is_jumping = False
        self.jump_offset = 0
    
    def attack(self):
        """Атака с учетом кулдауна и выносливости"""
        # Проверяем, не на кулдауне ли атака
        if self.attack_cooldown.is_active():
            return False
        
        # Проверяем выносливость
        if self.stamina >= ATTACK_COST:
            self.is_attacking = True
            self.attack_timer.start()
            self.attack_cooldown.start()  # Запускаем кулдаун
            self.stamina -= ATTACK_COST
            return True
        return False
    
    def take_damage(self, damage):
        self.health = max(0, self.health - damage)
        self.is_hurt = True
        self.hurt_timer.start()
    
    def handle_stamina(self, dt):
        if self.is_running:
            self.stamina = max(0, self.stamina - STAMINA_RUN_COST * dt)
        elif not self.is_running and self.stamina < PLAYER_MAX_STAMINA:
            self.stamina = min(PLAYER_MAX_STAMINA, self.stamina + STAMINA_REGEN * dt)
    
    def handle_health_regen(self, dt):
        if self.health < PLAYER_MAX_HEALTH and self.health > 0:
            self.health = min(PLAYER_MAX_HEALTH, self.health + HEALTH_REGEN * dt)
    
    def respawn(self):
        self.health = PLAYER_MAX_HEALTH
        self.stamina = PLAYER_MAX_STAMINA
        self.position = Vector2(TILE_SIZE * 2, TILE_SIZE * 2)
        self.is_jumping = False
        self.is_attacking = False
        self.jump_offset = 0
        # Сбрасываем кулдаун атаки
        self.attack_cooldown.active = False
    
    def get_visual_position(self):
        """Возвращает позицию для отрисовки с учетом эффекта прыжка"""
        return Vector2(
            self.position.x,
            self.position.y + self.jump_offset
        )
    
    def get_visual_center(self):
        """Возвращает визуальный центр игрока с учетом прыжка"""
        visual_pos = self.get_visual_position()
        return Vector2(
            visual_pos.x + self.width / 2,
            visual_pos.y + self.height / 2
        )
    
    def draw(self, screen, camera):
        visual_pos = self.get_visual_position()
        screen_pos = Vector2(
            visual_pos.x - camera.position.x,
            visual_pos.y - camera.position.y
        )
        
        # Цвет с учетом получения урона
        color = (255, 255, 255) if self.is_hurt else COLOR_PLAYER
        
        # Рисуем игрока
        pygame.draw.rect(screen, color, 
                        (screen_pos.x, screen_pos.y, self.width, self.height))
        
        # Рисуем атаку в направлении игрока
        if self.is_attacking:
            # Определяем направление атаки
            attack_offset = 40
            attack_width = 40
            attack_height = 6
            
            # Центр игрока
            center_x = screen_pos.x + self.width // 2
            center_y = screen_pos.y + self.height // 2
            
            # Рисуем линию атаки в зависимости от направления
            if self.direction.x > 0:  # Вправо
                start_x = screen_pos.x + self.width
                start_y = center_y
                end_x = start_x + attack_offset
                end_y = start_y
            elif self.direction.x < 0:  # Влево
                start_x = screen_pos.x
                start_y = center_y
                end_x = start_x - attack_offset
                end_y = start_y
            elif self.direction.y > 0:  # Вниз
                start_x = center_x
                start_y = screen_pos.y + self.height
                end_x = start_x
                end_y = start_y + attack_offset
            else:  # Вверх или по умолчанию
                start_x = center_x
                start_y = screen_pos.y
                end_x = start_x
                end_y = start_y - attack_offset
            
            pygame.draw.line(screen, (255, 200, 0), 
                           (start_x, start_y),
                           (end_x, end_y), attack_height)