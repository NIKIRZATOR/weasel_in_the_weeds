import pygame
import sys
import math

# Инициализация
pygame.init()

# Константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 64
PLAYER_SIZE = 32

# Цвета
COLOR_GRASS = (34, 139, 34)
COLOR_WALL = (139, 69, 19)
COLOR_WATER = (65, 105, 225)
COLOR_PATH = (210, 180, 140)
COLOR_STONE = (128, 128, 128)
COLOR_PLAYER = (255, 0, 0)
COLOR_HEALTH = (255, 0, 0)
COLOR_HEALTH_BG = (100, 0, 0)
COLOR_STAMINA = (255, 255, 0)

# Параметры игрока
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_STAMINA = 100

# Создаем окно
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Top-Down Tilemap с плавной камерой")
clock = pygame.time.Clock()

# СЛОЙ 1: ЗЕМЛЯ
ground_layer = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# СЛОЙ 2: ПРЕПЯТСТВИЯ
obstacle_layer = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

MAP_WIDTH = len(ground_layer[0])
MAP_HEIGHT = len(ground_layer)

# Позиция игрока (реальная)
player_x = TILE_SIZE * 2
player_y = TILE_SIZE * 2
player_speed = 200
player_run_speed = 350

# Визуальная позиция для отрисовки и камеры
visual_x = player_x
visual_y = player_y

# Система прыжка
is_jumping = False
jump_timer = 0
jump_duration = 0.3
jump_start_x = 0
jump_start_y = 0
jump_end_x = 0
jump_end_y = 0

# Здоровье и выносливость
player_health = PLAYER_MAX_HEALTH
player_stamina = PLAYER_MAX_STAMINA
stamina_regen = 50
stamina_run_cost = 80
stamina_jump_cost = 20

# Атака
is_attacking = False
attack_timer = 0
attack_duration = 0.2
attack_cooldown = 0
attack_cooldown_duration = 0.4

is_running = False
is_hurt = False
hurt_timer = 0

# Камера
camera_x = 0
camera_y = 0

def check_collision(x, y, ignore_jump_target=False):
    """Проверяет коллизию со стенами и препятствиями"""
    corners = [(x, y), (x + PLAYER_SIZE, y), 
               (x, y + PLAYER_SIZE), (x + PLAYER_SIZE, y + PLAYER_SIZE)]
    
    for cx, cy in corners:
        tile_x = int(cx // TILE_SIZE)
        tile_y = int(cy // TILE_SIZE)
        
        if tile_x < 0 or tile_x >= MAP_WIDTH or tile_y < 0 or tile_y >= MAP_HEIGHT:
            return True
        
        if ground_layer[tile_y][tile_x] == 1:
            return True
        
        obstacle = obstacle_layer[tile_y][tile_x]
        if obstacle == 1 and not ignore_jump_target:
            if not is_jumping:
                return True
        elif obstacle == 2:
            return True
    
    return False

def try_jump(direction_x, direction_y):
    """Попытка прыгнуть через препятствие"""
    global is_jumping, jump_timer, jump_start_x, jump_start_y, jump_end_x, jump_end_y, player_stamina
    
    if is_jumping or player_stamina < stamina_jump_cost:
        return False
    
    if direction_x == 0 and direction_y == 0:
        return False
    
    length = math.sqrt(direction_x**2 + direction_y**2)
    dir_x = direction_x / length
    dir_y = direction_y / length
    
    jump_distance = TILE_SIZE * 1.5
    new_x = player_x + dir_x * jump_distance
    new_y = player_y + dir_y * jump_distance
    
    if not check_collision(new_x, new_y, ignore_jump_target=True):
        is_jumping = True
        jump_timer = jump_duration
        jump_start_x = player_x
        jump_start_y = player_y
        jump_end_x = new_x
        jump_end_y = new_y
        player_stamina -= stamina_jump_cost
        return True
    
    return False

def attack():
    global is_attacking, attack_timer, attack_cooldown, player_stamina
    if attack_cooldown <= 0 and player_stamina >= 10:
        is_attacking = True
        attack_timer = attack_duration
        attack_cooldown = attack_cooldown_duration
        player_stamina -= 10

def take_damage(damage):
    global player_health, is_hurt, hurt_timer
    player_health = max(0, player_health - damage)
    is_hurt = True
    hurt_timer = 0.2

def get_visual_position():
    """Возвращает визуальную позицию игрока для отрисовки"""
    if is_jumping:
        t = 1 - (jump_timer / jump_duration)
        # Параболическая траектория
        visual_x = jump_start_x + (jump_end_x - jump_start_x) * t
        visual_y = jump_start_y + (jump_end_y - jump_start_y) * t - math.sin(t * math.pi) * 40
        return visual_x, visual_y
    else:
        return player_x, player_y

def draw_layers():
    """Рисует оба слоя"""
    start_x = int(max(0, camera_x // TILE_SIZE))
    end_x = int(min(MAP_WIDTH, (camera_x + SCREEN_WIDTH) // TILE_SIZE + 1))
    start_y = int(max(0, camera_y // TILE_SIZE))
    end_y = int(min(MAP_HEIGHT, (camera_y + SCREEN_HEIGHT) // TILE_SIZE + 1))
    
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            screen_x = x * TILE_SIZE - camera_x
            screen_y = y * TILE_SIZE - camera_y
            
            tile_type = ground_layer[y][x]
            if tile_type == 0:
                color = COLOR_GRASS
            elif tile_type == 1:
                color = COLOR_WALL
            elif tile_type == 2:
                color = COLOR_WATER
            elif tile_type == 3:
                color = COLOR_PATH
            else:
                color = (255, 0, 255)
            
            pygame.draw.rect(screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(screen, (0, 0, 0), (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)
            
            obstacle = obstacle_layer[y][x]
            if obstacle == 1:
                pygame.draw.ellipse(screen, COLOR_STONE, 
                                   (screen_x + 10, screen_y + 20, TILE_SIZE - 20, TILE_SIZE - 30))
                pygame.draw.ellipse(screen, (80, 80, 80), 
                                   (screen_x + 15, screen_y + 25, TILE_SIZE - 30, TILE_SIZE - 40), 2)

def draw_player():
    """Рисует игрока"""
    visual_x, visual_y = get_visual_position()
    player_screen_x = visual_x - camera_x
    player_screen_y = visual_y - camera_y
    
    player_color = COLOR_PLAYER
    if is_hurt:
        player_color = (255, 255, 255)
    
    pygame.draw.rect(screen, player_color, 
                    (player_screen_x, player_screen_y, PLAYER_SIZE, PLAYER_SIZE))
    
    if is_attacking:
        attack_x = player_screen_x + PLAYER_SIZE
        attack_y = player_screen_y + PLAYER_SIZE // 2
        pygame.draw.line(screen, (255, 200, 0), 
                        (attack_x, attack_y),
                        (attack_x + 40, attack_y), 6)

def draw_ui():
    """Рисует интерфейс"""
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    health_width = 200
    health_percent = player_health / PLAYER_MAX_HEALTH
    pygame.draw.rect(screen, COLOR_HEALTH_BG, (10, 10, health_width, 20))
    pygame.draw.rect(screen, COLOR_HEALTH, (10, 10, health_width * health_percent, 20))
    
    stamina_width = 200
    stamina_percent = player_stamina / PLAYER_MAX_STAMINA
    pygame.draw.rect(screen, (50, 50, 0), (10, 35, stamina_width, 15))
    pygame.draw.rect(screen, COLOR_STAMINA, (10, 35, stamina_width * stamina_percent, 15))
    
    health_text = font.render(f"HP: {int(player_health)}", True, (255, 255, 255))
    stamina_text = font.render(f"ST: {int(player_stamina)}", True, (255, 255, 255))
    screen.blit(health_text, (220, 8))
    screen.blit(stamina_text, (220, 33))
    
    controls = small_font.render("WASD - move | SHIFT - run | SPACE - jump over stones | F - attack", 
                                  True, (200, 200, 200))
    screen.blit(controls, (10, SCREEN_HEIGHT - 30))

def update_camera():
    """Обновляет камеру по визуальной позиции игрока"""
    global camera_x, camera_y
    
    visual_x, visual_y = get_visual_position()
    
    target_x = visual_x + PLAYER_SIZE // 2 - SCREEN_WIDTH // 2
    target_y = visual_y + PLAYER_SIZE // 2 - SCREEN_HEIGHT // 2
    
    max_camera_x = MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH
    max_camera_y = MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT
    
    camera_x = max(0, min(target_x, max_camera_x))
    camera_y = max(0, min(target_y, max_camera_y))

# Игровой цикл
running = True
while running:
    dt = clock.tick(60) / 1000.0
    if dt > 0.033: dt = 0.033
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_f:
                attack()
            elif event.key == pygame.K_SPACE and not is_jumping:
                keys = pygame.key.get_pressed()
                dx = 0
                dy = 0
                if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -1
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = 1
                if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -1
                if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = 1
                
                if dx != 0 or dy != 0:
                    try_jump(dx, dy)
    
    # Обновление прыжка
    if is_jumping:
        jump_timer -= dt
        if jump_timer <= 0:
            player_x = jump_end_x
            player_y = jump_end_y
            is_jumping = False
    
    # Управление
    if not is_jumping:
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = 1
        
        current_speed = player_run_speed if keys[pygame.K_LSHIFT] and player_stamina > 0 else player_speed
        is_running = current_speed == player_run_speed and (dx != 0 or dy != 0)
        
        if dx != 0 or dy != 0:
            if dx != 0 and dy != 0:
                current_speed *= 0.707
            
            new_x = player_x + dx * current_speed * dt
            new_y = player_y + dy * current_speed * dt
            
            if not check_collision(new_x, player_y):
                player_x = new_x
            if not check_collision(player_x, new_y):
                player_y = new_y
        
        if is_running:
            player_stamina = max(0, player_stamina - stamina_run_cost * dt)
        
        if not is_running and player_stamina < PLAYER_MAX_STAMINA:
            player_stamina = min(PLAYER_MAX_STAMINA, player_stamina + stamina_regen * dt)
    
    # Регенерация здоровья
    if player_health < PLAYER_MAX_HEALTH and player_health > 0:
        player_health = min(PLAYER_MAX_HEALTH, player_health + 10 * dt)
    
    # Таймеры
    if is_attacking:
        attack_timer -= dt
        if attack_timer <= 0:
            is_attacking = False
    
    if attack_cooldown > 0:
        attack_cooldown -= dt
    
    if is_hurt:
        hurt_timer -= dt
        if hurt_timer <= 0:
            is_hurt = False
    
    # Смерть
    if player_health <= 0:
        player_health = PLAYER_MAX_HEALTH
        player_stamina = PLAYER_MAX_STAMINA
        player_x = TILE_SIZE * 2
        player_y = TILE_SIZE * 2
    
    # Обновление камеры (теперь по визуальной позиции)
    update_camera()
    
    # Отрисовка
    screen.fill((0, 0, 0))
    draw_layers()
    draw_player()
    draw_ui()
    
    pygame.display.flip()

pygame.quit()
sys.exit()