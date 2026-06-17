import pygame

from game.core.camera import Camera
from game.core.vector import Vector2
from game.entities.enemy import MeleeEnemy, RangedEnemy
from game.entities.player import Player
from game.items import create_item_stack
from game.objects import create_world_object
from game.scenes.base import Scene
from game.ui.hud import HUD
from game.world.collision import CollisionSystem
from game.world.level import load_level
from game.world.tilemap import TileMap
from settings import COLORS


class GameScene(Scene):
    def __init__(self, app, level_path):
        self.app = app
        self.level = load_level(level_path)
        pygame.display.set_caption(f"Weales in the weeds RPG - {self.level.name}")

        self.tilemap = TileMap(
            self.level.ground_layer,
            self.level.obstacle_layer,
            tile_size=self.level.tile_size,
            tileset_image_path=self.level.tileset_image_path,
        )
        self.collision_system = CollisionSystem(self.tilemap)

        spawn_x, spawn_y = self.level.player_spawn
        spawn_world_x = self.level.tile_size * spawn_x
        spawn_world_y = self.level.tile_size * spawn_y
        self.player = Player(
            spawn_world_x,
            spawn_world_y,
            spawn_x=spawn_world_x,
            spawn_y=spawn_world_y,
        )
        self.world_objects, self.enemies = self._load_world_objects()
        self.collision_system.set_objects(self.world_objects)
        self._player_attack_applied = False

        world_width = self.tilemap.width * self.tilemap.tile_size
        world_height = self.tilemap.height * self.tilemap.tile_size
        self.camera = Camera(world_width, world_height)
        self.hud = HUD()
        self.info_font = pygame.font.Font(None, 28)
        self.interaction_font = pygame.font.Font(None, 30)
        self.last_interaction_message = ""
        self.last_interaction_timer = 0.0
        self.current_interaction_target = None

    def _load_world_objects(self):
        world_objects = []
        enemies = []
        for raw_object in self.level.objects:
            object_type = raw_object.get("type")
            if object_type == "enemy_melee":
                enemies.append(self._create_enemy(raw_object, MeleeEnemy))
                continue
            if object_type == "enemy_ranged":
                enemies.append(self._create_enemy(raw_object, RangedEnemy))
                continue

            world_object = create_world_object(raw_object, self.level.tile_size)
            if world_object is not None:
                world_objects.append(world_object)
        return world_objects, enemies

    def _create_enemy(self, raw_object, enemy_class):
        width = raw_object.get("width", 1) * self.level.tile_size
        height = raw_object.get("height", 1) * self.level.tile_size
        x = raw_object.get("x", 0) * self.level.tile_size
        y = raw_object.get("y", 0) * self.level.tile_size
        properties = raw_object.get("properties", {})

        return enemy_class(
            x,
            y,
            width,
            height,
            name=raw_object.get("name", enemy_class.__name__),
            max_health=int(properties.get("health", raw_object.get("health", 20))),
            speed=int(properties.get("speed", raw_object.get("speed", 80))),
            damage=int(properties.get("damage", raw_object.get("damage", 4))),
            **self._enemy_specific_kwargs(raw_object, enemy_class),
        )

    def _enemy_specific_kwargs(self, raw_object, enemy_class):
        properties = raw_object.get("properties", {})
        if enemy_class is MeleeEnemy:
            return {
                "melee_range": int(properties.get("melee_range", raw_object.get("melee_range", 44))),
                "attack_cooldown": float(properties.get("attack_cooldown", raw_object.get("attack_cooldown", 1.0))),
            }

        return {
            "preferred_distance": int(properties.get("preferred_distance", raw_object.get("preferred_distance", 180))),
            "min_distance": int(properties.get("min_distance", raw_object.get("min_distance", 120))),
            "attack_range": int(properties.get("attack_range", raw_object.get("attack_range", 260))),
            "attack_cooldown": float(properties.get("attack_cooldown", raw_object.get("attack_cooldown", 1.4))),
        }

    def open_pause_menu(self):
        from game.scenes.pause_menu_scene import PauseMenuScene

        self.app.set_scene(PauseMenuScene(self.app, self))

    def open_inventory(self):
        from game.scenes.inventory_scene import InventoryScene

        self.app.set_scene(InventoryScene(self.app, self))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.open_pause_menu()
                elif event.key == pygame.K_i:
                    self.open_inventory()
                elif event.key == pygame.K_e:
                    self.try_interact()
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    self.player.select_hotbar_slot(event.key - pygame.K_1)
                elif event.key == pygame.K_SPACE and not self.player.is_jumping:
                    keys = pygame.key.get_pressed()
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

                    if dx != 0 or dy != 0:
                        self.player.try_jump(Vector2(dx, dy), self)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                target = self._mouse_world_position(event.pos)
                self.player.attack_towards(target.x, target.y)

    def check_collision(self, x, y, entity, ignore_jump=False):
        if self.collision_system.check_collision(x, y, entity, ignore_jump):
            return True

        if entity is self.player and self._collides_with_enemies(x, y, entity):
            return True

        return False

    def try_pickup_object(self, pickable_object):
        properties = pickable_object.properties or {}
        item_id = properties.get("item_id") or pickable_object.name
        quantity = int(properties.get("quantity", 1))
        coins = int(properties.get("coins", 0))

        item_stack = None
        if item_id is not None:
            item_stack = create_item_stack(item_id, quantity)
            if item_stack is None and coins <= 0:
                self.last_interaction_message = f"Неизвестный предмет: {item_id}"
                self.last_interaction_timer = 1.5
                return False

        currency_amount = coins
        if item_stack is not None and item_stack.kind.value == "currency":
            currency_amount += item_stack.quantity

        if not self.player.pickup_item(item_stack=item_stack, coins=coins):
            self.last_interaction_message = "Инвентарь переполнен"
            self.last_interaction_timer = 1.5
            return False

        pickable_object.is_picked = True
        pickable_object.is_active = True
        pickable_object.color = COLORS["PICKABLE_PICKED"]

        if item_stack is not None and item_stack.kind.value == "currency":
            self.last_interaction_message = f"Подобрано: {currency_amount} монет"
        elif item_stack is not None and coins > 0:
            self.last_interaction_message = f"Подобрано: {item_stack.name} x{item_stack.quantity} + {coins} монет"
        elif item_stack is not None:
            self.last_interaction_message = f"Подобрано: {item_stack.name} x{item_stack.quantity}"
        elif coins > 0:
            self.last_interaction_message = f"Подобрано: {coins} монет"
        else:
            self.last_interaction_message = f"Подобрано: {pickable_object.name}"
        self.last_interaction_timer = 1.5
        return True

    def try_interact(self):
        target = self._find_interaction_target()
        if target is None:
            self.last_interaction_message = "Рядом нет объекта для взаимодействия"
            self.last_interaction_timer = 1.0
            return False

        result = target.interact(self.player, self)
        if result and getattr(target, "is_picked", False):
            self.world_objects = [obj for obj in self.world_objects if obj is not target]
            self.collision_system.set_objects(self.world_objects)
        return result

    def _find_interaction_target(self):
        player_zone = self.player.get_interaction_rect()
        candidates = []
        for world_object in self.world_objects:
            if not world_object.is_interactable:
                continue

            object_zone = world_object.get_interaction_rect()
            if _rects_intersect(player_zone, object_zone):
                candidates.append(world_object)

        if not candidates:
            return None

        player_center = self.player.get_center()
        return min(candidates, key=lambda obj: _distance_squared(player_center, obj.get_center()))

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self)
        self._update_enemies(dt)
        self._resolve_player_enemy_overlaps()
        self._apply_player_attack()
        screen_width, screen_height = self.app.get_screen_size()
        self.camera.update(self.player, screen_width, screen_height)
        self.current_interaction_target = self._find_interaction_target()
        if self.last_interaction_timer > 0:
            self.last_interaction_timer = max(0.0, self.last_interaction_timer - dt)
            if self.last_interaction_timer == 0.0:
                self.last_interaction_message = ""

    def _update_enemies(self, dt):
        alive_enemies = []
        for enemy in self.enemies:
            enemy.update(dt, self)
            if not enemy.is_dead:
                alive_enemies.append(enemy)
        self.enemies = alive_enemies

    def _collides_with_enemies(self, x, y, entity, ignored_enemy=None):
        hitbox = entity.get_hitbox_at(x, y)
        for enemy in self.enemies:
            if enemy is entity or enemy is ignored_enemy or enemy.is_dead:
                continue
            if _rects_intersect(hitbox, enemy.get_hitbox_rect()):
                return True
        return False

    def _resolve_player_enemy_overlaps(self):
        for enemy in self.enemies:
            if enemy.is_dead:
                continue

            overlap = _get_rect_overlap(self.player.get_hitbox_rect(), enemy.get_hitbox_rect())
            if overlap is None:
                continue

            push_x, push_y = overlap
            self._separate_player_and_enemy(enemy, push_x, push_y)

    def _separate_player_and_enemy(self, enemy, push_x, push_y):
        player_dx = -push_x * 0.65
        player_dy = -push_y * 0.65
        enemy_dx = push_x * 0.35
        enemy_dy = push_y * 0.35

        player_moved = self._try_move_entity(self.player, player_dx, player_dy)
        enemy_moved = self._try_move_entity(enemy, enemy_dx, enemy_dy, ignored_enemy=enemy)

        if player_moved or enemy_moved:
            return

        if self._try_move_entity(self.player, -push_x, -push_y):
            return

        self._try_move_entity(enemy, push_x, push_y, ignored_enemy=enemy)

    def _try_move_entity(self, entity, dx, dy, ignored_enemy=None):
        moved = False
        if abs(dx) > 0:
            next_x = entity.position.x + dx
            if self._can_place_entity(entity, next_x, entity.position.y, ignored_enemy):
                entity.position.x = next_x
                moved = True
        if abs(dy) > 0:
            next_y = entity.position.y + dy
            if self._can_place_entity(entity, entity.position.x, next_y, ignored_enemy):
                entity.position.y = next_y
                moved = True
        return moved

    def _can_place_entity(self, entity, x, y, ignored_enemy=None):
        if self.collision_system.check_collision(x, y, entity):
            return False
        if entity is self.player:
            if self._player_collides_with_enemy(x, y, ignored_enemy):
                return False
        return True

    def _player_collides_with_enemy(self, x, y, ignored_enemy=None):
        hitbox = self.player.get_hitbox_at(x, y)
        for enemy in self.enemies:
            if enemy is ignored_enemy or enemy.is_dead:
                continue
            if _rects_intersect(hitbox, enemy.get_hitbox_rect()):
                return True
        return False

    def _apply_player_attack(self):
        if self.player.is_attacking:
            if self._player_attack_applied:
                return

            damage = max(1, int(self.player.get_attack()))
            attack_origin, attack_end, attack_thickness = self._get_player_attack_segment()
            for enemy in self.enemies:
                if enemy.is_dead:
                    continue
                if _segment_hits_rect(attack_origin, attack_end, attack_thickness, enemy.get_hitbox_rect()):
                    enemy.take_damage(damage)
            self._player_attack_applied = True
            return

        self._player_attack_applied = False

    def _get_player_attack_segment(self):
        center = self.player.get_center()
        aim = self.player.aim_direction.normalize() if self.player.aim_direction.length() > 0 else Vector2(1, 0)
        start = Vector2(center.x + aim.x * 12, center.y + aim.y * 12)
        end = Vector2(start.x + aim.x * 40, start.y + aim.y * 40)
        return start, end, 42

    def _mouse_world_position(self, mouse_pos):
        return Vector2(
            mouse_pos[0] + self.camera.position.x,
            mouse_pos[1] + self.camera.position.y,
        )

    def draw(self):
        screen_width, _ = self.app.get_screen_size()
        self.app.screen.fill(COLORS["BLACK"])
        self.tilemap.draw(self.app.screen, self.camera)
        for world_object in self.world_objects:
            world_object.draw(self.app.screen, self.camera)
        for enemy in self.enemies:
            enemy.draw(self.app.screen, self.camera)
        self.player.draw(self.app.screen, self.camera)
        self.hud.draw(self.app.screen, self.player)
        if self.current_interaction_target is not None:
            self._draw_interaction_prompt(self.current_interaction_target)
        if self.last_interaction_message:
            message = self.info_font.render(self.last_interaction_message, True, COLORS["WHITE"])
            self.app.screen.blit(
                message,
                message.get_rect(center=(screen_width // 2, 24)),
            )

    def _draw_interaction_prompt(self, world_object):
        prompt_text = self.interaction_font.render("E", True, COLORS["WHITE"])
        padding_x = 10
        padding_y = 6
        bubble_width = prompt_text.get_width() + padding_x * 2
        bubble_height = prompt_text.get_height() + padding_y * 2

        bubble_x = (
            world_object.position.x
            + world_object.width / 2
            - bubble_width / 2
            - self.camera.position.x
        )
        bubble_y = world_object.position.y - bubble_height - 10 - self.camera.position.y

        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
        pygame.draw.rect(
            self.app.screen,
            (30, 30, 36),
            bubble_rect,
            border_radius=8,
        )
        pygame.draw.rect(
            self.app.screen,
            COLORS["INTERACTABLE_ACTIVE"],
            bubble_rect,
            width=2,
            border_radius=8,
        )
        self.app.screen.blit(
            prompt_text,
            prompt_text.get_rect(center=bubble_rect.center),
        )


def _rects_intersect(rect_a, rect_b):
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b
    return (
        ax < bx + bw
        and ax + aw > bx
        and ay < by + bh
        and ay + ah > by
    )


def _get_rect_overlap(rect_a, rect_b):
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b
    if not _rects_intersect(rect_a, rect_b):
        return None

    center_ax = ax + aw / 2
    center_ay = ay + ah / 2
    center_bx = bx + bw / 2
    center_by = by + bh / 2

    overlap_x = min(ax + aw, bx + bw) - max(ax, bx)
    overlap_y = min(ay + ah, by + bh) - max(ay, by)

    if overlap_x <= overlap_y:
        direction_x = 1 if center_bx >= center_ax else -1
        return (overlap_x * direction_x, 0)

    direction_y = 1 if center_by >= center_ay else -1
    return (0, overlap_y * direction_y)


def _distance_squared(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    return dx * dx + dy * dy


def _segment_hits_rect(start, end, thickness, rect):
    rx, ry, rw, rh = rect
    center = Vector2(rx + rw / 2, ry + rh / 2)
    radius = max(rw, rh) / 2
    return _distance_point_to_segment(center, start, end) <= radius + thickness / 2


def _distance_point_to_segment(point, start, end):
    dx = end.x - start.x
    dy = end.y - start.y
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return ((point.x - start.x) ** 2 + (point.y - start.y) ** 2) ** 0.5

    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    closest_x = start.x + t * dx
    closest_y = start.y + t * dy
    return ((point.x - closest_x) ** 2 + (point.y - closest_y) ** 2) ** 0.5
