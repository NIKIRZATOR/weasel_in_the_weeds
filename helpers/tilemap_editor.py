import pygame

# Настройки
MAP_WIDTH = 30
MAP_HEIGHT = 30
TILE_SIZE = 40
SCREEN_SIZE = (800, 600)

# Данные карты (2D массив)
map_data = [[0 for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)]

# Типы тайлов
TILES = {
    0: {"name": "трава", "color": (34, 139, 34), "walkable": True},
    1: {"name": "стена", "color": (139, 69, 19), "walkable": False},
    2: {"name": "вода", "color": (65, 105, 225), "walkable": False},
    3: {"name": "тропинка", "color": (210, 180, 140), "walkable": True},
}

current_tile = 0  # Выбранный тайл

def draw_grid():
    """Рисует сетку для удобства"""
    for x in range(0, SCREEN_SIZE[0], TILE_SIZE):
        pygame.draw.line(screen, (100, 100, 100), (x, 0), (x, SCREEN_SIZE[1]))
    for y in range(0, SCREEN_SIZE[1], TILE_SIZE):
        pygame.draw.line(screen, (100, 100, 100), (0, y), (SCREEN_SIZE[0], y))

def draw_map():
    """Рисует карту"""
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            color = TILES[map_data[y][x]]["color"]
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)  # граница

def save_map(filename):
    """Сохраняет карту в файл"""
    with open(filename, 'w') as f:
        for row in map_data:
            f.write(' '.join(str(cell) for cell in row) + '\n')
    print(f"Карта сохранена в {filename}")

def load_map(filename):
    """Загружает карту из файла"""
    global map_data
    with open(filename, 'r') as f:
        map_data = [list(map(int, line.split())) for line in f.readlines()]
    print(f"Карта загружена из {filename}")

# Игровой цикл редактора
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Выбор тайла цифрами 0-9
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_0: current_tile = 0
            elif event.key == pygame.K_1: current_tile = 1
            elif event.key == pygame.K_2: current_tile = 2
            elif event.key == pygame.K_3: current_tile = 3
            elif event.key == pygame.K_s: save_map("mymap.txt")
            elif event.key == pygame.K_l: load_map("mymap.txt")
        
        # Рисование мышкой
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            tile_x = mouse_x // TILE_SIZE
            tile_y = mouse_y // TILE_SIZE
            if 0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT:
                map_data[tile_y][tile_x] = current_tile
    
    # Отрисовка
    screen.fill((50, 50, 50))
    draw_map()
    draw_grid()
    
    # Отображаем текущий выбранный тайл
    font = pygame.font.Font(None, 36)
    text = font.render(f"Current tile: {TILES[current_tile]['name']}", True, (255, 255, 255))
    screen.blit(text, (10, 10))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()