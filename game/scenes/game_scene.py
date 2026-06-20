from pathlib import Path

import pygame

from game.core.camera import Camera
from game.core.vector import Vector2
from game.entities.enemy import MeleeEnemy, RangedEnemy
from game.entities.player import Player
from game.items import create_item_stack
from game.localization import get_localizer
from game.objects import create_world_object
from game.scenes.base import Scene
from game.ui.hud import HUD
from game.world.collision import CollisionSystem
from game.world.level import load_level
from game.world.tilemap import TileMap
from settings import COLORS, LEVELS_DIR


TRANSITION_FADE_DURATION = 0.45
DAMAGE_NUMBER_DURATION = 0.75
DAMAGE_NUMBER_RISE_SPEED = 52
CHARGED_ATTACK_THRESHOLD = 1.0


class GameScene(Scene):
    def __init__(self, app, level_path, player=None, target_spawn=None):
        self.app = app
        self.localizer = get_localizer()
        self.level_path = level_path
        self.level_key = Path(level_path).name
        self.level = load_level(level_path)
        self._update_window_caption()

        self.tilemap = TileMap(
            self.level.ground_layer,
            self.level.obstacle_layer,
            tile_size=self.level.tile_size,
        )
        self.collision_system = CollisionSystem(self.tilemap)

        spawn_x, spawn_y = target_spawn if target_spawn is not None else self.level.player_spawn
        spawn_world_x = self.level.tile_size * spawn_x
        spawn_world_y = self.level.tile_size * spawn_y
        if player is None:
            self.player = Player(
                spawn_world_x,
                spawn_world_y,
                spawn_x=spawn_world_x,
                spawn_y=spawn_world_y,
            )
        else:
            self.player = player
            self.player.move_to_spawn(spawn_world_x, spawn_world_y)
        self.world_objects, self.enemies = self._load_world_objects()
        self.collision_system.set_objects(self.world_objects)
        self._player_attack_applied = False
        self.transition_target_level = None
        self.transition_target_spawn = None
        self.transition_timer = 0.0
        self.damage_numbers = []
        self.player_projectiles = []
        self.mouse_buttons_held = set()
        self.mouse_hold_time = 0.0
        self.charged_combo_fired = False

        world_width = self.tilemap.width * self.tilemap.tile_size
        world_height = self.tilemap.height * self.tilemap.tile_size
        self.camera = Camera(world_width, world_height)
        self.hud = HUD()
        self.info_font = pygame.font.Font(None, 28)
        self.interaction_font = pygame.font.Font(None, 30)
        self.last_interaction_message = ""
        self.last_interaction_timer = 0.0
        self.current_interaction_target = None

    def on_language_changed(self):
        self._update_window_caption()
        self.hud.on_language_changed()

    def _update_window_caption(self):
        pygame.display.set_caption(
            self.localizer.t(
                "ui.window.game_title",
                level=self._localized_level_name(),
            )
        )

    def _localized_level_name(self):
        key = f"ui.levels.{Path(self.level_path).stem}"
        translated = self.localizer.t(key)
        return translated if translated != key else self.level.name

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

    def open_map(self):
        from game.scenes.map_scene import MapScene

        self.app.set_scene(MapScene(self.app, self))

    def open_crafting(self):
        from game.scenes.crafting_scene import CraftingScene

        self.app.set_scene(CraftingScene(self.app, self))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.app.running = False
            elif self.transition_target_level is not None:
                continue
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.open_pause_menu()
                elif event.key == pygame.K_i:
                    self.open_inventory()
                elif event.key == pygame.K_m:
                    if self.player.can_open_map():
                        self.open_map()
                    else:
                        self.last_interaction_message = self.localizer.t("pickup.no_map")
                        self.last_interaction_timer = 1.5
                elif event.key == pygame.K_k:
                    self.open_crafting()
                elif event.key == pygame.K_e:
                    self.try_interact()
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    self.player.select_hotbar_slot(event.key - pygame.K_1)
                elif event.key == pygame.K_SPACE and not self.player.is_jumping:
                    keys = pygame.key.get_pressed()
                    direction = self._read_movement_direction(keys)

                    if direction.length() > 0:
                        self.player.try_jump(direction, self)
                elif event.key == pygame.K_LALT:
                    keys = pygame.key.get_pressed()
                    self.player.try_dash(self._read_movement_direction(keys))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                self.mouse_buttons_held.add(event.button)
                if self.mouse_buttons_held == {1, 3}:
                    self.mouse_hold_time = 0.0
                    self.charged_combo_fired = False
            elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
                if self.charged_combo_fired:
                    self.mouse_buttons_held.discard(event.button)
                    if self.mouse_buttons_held != {1, 3}:
                        self.mouse_hold_time = 0.0
                        self.charged_combo_fired = False
                    continue

                if self.mouse_buttons_held == {1, 3}:
                    self.mouse_buttons_held.discard(event.button)
                    self.mouse_hold_time = 0.0
                    continue

                target = self._mouse_world_position(event.pos)
                attack_kind = "light" if event.button == 1 else "heavy"
                self.player.attack_towards(target.x, target.y, attack_kind=attack_kind)
                self.mouse_buttons_held.discard(event.button)
                self.mouse_hold_time = 0.0

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
        knowledge_shards = int(properties.get("knowledge_shards", 0))

        item_stack = None
        if item_id is not None:
            item_stack = create_item_stack(item_id, quantity)
            if item_stack is None and coins <= 0 and knowledge_shards <= 0:
                self.last_interaction_message = self.localizer.t("pickup.unknown_item", item_id=item_id)
                self.last_interaction_timer = 1.5
                return False

        currency_amount = coins
        currency_wallet = None
        if item_stack is not None and item_stack.kind.value == "currency":
            currency_wallet = item_stack.definition.wallet_key
            if currency_wallet == "coins":
                currency_amount += item_stack.quantity

        if not self.player.pickup_item(item_stack=item_stack, coins=coins):
            self.last_interaction_message = self.localizer.t("pickup.inventory_full")
            self.last_interaction_timer = 1.5
            return False

        if knowledge_shards > 0:
            self.player.add_knowledge_shards(knowledge_shards)

        pickable_object.is_picked = True
        pickable_object.is_active = True
        pickable_object.color = COLORS["PICKABLE_PICKED"]

        if item_stack is not None and item_stack.kind.value == "currency":
            if currency_wallet == "coins":
                self.last_interaction_message = self.localizer.t("pickup.picked_currency_coins", amount=currency_amount)
            elif currency_wallet == "knowledge_shards":
                self.last_interaction_message = self.localizer.t(
                    "pickup.picked_currency_knowledge_shards",
                    amount=item_stack.quantity,
                )
            else:
                self.last_interaction_message = self.localizer.t(
                    "pickup.picked_item",
                    name=item_stack.name,
                    quantity=item_stack.quantity,
                )
            self.last_interaction_timer = 1.5
            return True
        if item_stack is not None and coins > 0:
            self.last_interaction_message = self.localizer.t(
                "pickup.picked_item_with_coins",
                name=item_stack.name,
                quantity=item_stack.quantity,
                coins=coins,
            )
            self.last_interaction_timer = 1.5
            return True
        if item_stack is not None:
            self.last_interaction_message = self.localizer.t(
                "pickup.picked_item",
                name=item_stack.name,
                quantity=item_stack.quantity,
            )
            self.last_interaction_timer = 1.5
            return True
        if coins > 0:
            self.last_interaction_message = self.localizer.t("pickup.picked_coins", coins=coins)
            self.last_interaction_timer = 1.5
            return True
        if knowledge_shards > 0:
            self.last_interaction_message = self.localizer.t(
                "pickup.picked_currency_knowledge_shards",
                amount=knowledge_shards,
            )
            self.last_interaction_timer = 1.5
            return True

        if item_stack is not None and item_stack.kind.value == "currency":
            self.last_interaction_message = self.localizer.t("pickup.picked_currency_coins", amount=currency_amount)
        elif item_stack is not None and coins > 0:
            self.last_interaction_message = self.localizer.t(
                "pickup.picked_item_with_coins",
                name=item_stack.name,
                quantity=item_stack.quantity,
                coins=coins,
            )
        elif item_stack is not None:
            self.last_interaction_message = self.localizer.t(
                "pickup.picked_item",
                name=item_stack.name,
                quantity=item_stack.quantity,
            )
        elif coins > 0:
            self.last_interaction_message = self.localizer.t("pickup.picked_coins", coins=coins)
        else:
            self.last_interaction_message = self.localizer.t("pickup.picked_name", name=pickable_object.name)
        self.last_interaction_timer = 1.5
        return True

    def try_interact(self):
        target = self._find_interaction_target()
        if target is None:
            self.last_interaction_message = self.localizer.t("pickup.no_target")
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
        if self.transition_target_level is not None:
            self._update_level_transition(dt)
            return

        keys = pygame.key.get_pressed()
        if self.mouse_buttons_held == {1, 3}:
            self.mouse_hold_time += dt
            if not self.charged_combo_fired and self.mouse_hold_time >= CHARGED_ATTACK_THRESHOLD:
                mouse_pos = pygame.mouse.get_pos()
                target = self._mouse_world_position(mouse_pos)
                if self.player.attack_towards(target.x, target.y, attack_kind="charged"):
                    self.charged_combo_fired = True
        else:
            self.mouse_hold_time = 0.0
            self.charged_combo_fired = False
        self.player.update(dt, keys, self)
        self._update_map_reveal()
        self._update_grass_hide_zones()
        self._update_checkpoints()
        self._update_enemies(dt)
        self._update_player_projectiles(dt)
        self._resolve_player_enemy_overlaps()
        self._apply_player_attack()
        self._update_damage_numbers(dt)
        self._check_level_transitions()
        screen_width, screen_height = self.app.get_screen_size()
        self.camera.update(self.player, screen_width, screen_height)
        self.current_interaction_target = self._find_interaction_target()
        if self.last_interaction_timer > 0:
            self.last_interaction_timer = max(0.0, self.last_interaction_timer - dt)
            if self.last_interaction_timer == 0.0:
                self.last_interaction_message = ""

    def _update_checkpoints(self):
        for world_object in self.world_objects:
            if not getattr(world_object, "is_checkpoint", False):
                continue
            world_object.activate(self.player, self)

    def _update_map_reveal(self):
        player_center = self.player.get_center()
        tile_x = int(player_center.x // self.level.tile_size)
        tile_y = int(player_center.y // self.level.tile_size)
        self.player.reveal_map_area(
            self.level_key,
            self.level.width,
            self.level.height,
            tile_x,
            tile_y,
            radius=1,
        )

    def _update_grass_hide_zones(self):
        player_hitbox = self.player.get_hitbox_rect()
        self.player.is_hidden = False
        for world_object in self.world_objects:
            if not getattr(world_object, "is_grass_hide_zone", False):
                continue
            if not world_object.can_hide(self.player):
                continue
            if _rects_intersect(player_hitbox, world_object.get_hitbox_rect()):
                self.player.is_hidden = True
                return

    def _check_level_transitions(self):
        player_hitbox = self.player.get_hitbox_rect()
        for world_object in self.world_objects:
            if not getattr(world_object, "is_transition", False):
                continue
            if not _rects_intersect(player_hitbox, world_object.get_hitbox_rect()):
                continue
            if not world_object.can_activate(self.player):
                self.last_interaction_message = world_object.get_block_message()
                self.last_interaction_timer = 1.0
                return

            target_level = world_object.get_target_level()
            if not target_level:
                self.last_interaction_message = self.localizer.t("pickup.transition_missing_target")
                self.last_interaction_timer = 1.0
                return

            self.transition_target_level = LEVELS_DIR / target_level
            self.transition_target_spawn = world_object.get_target_spawn()
            self.transition_timer = 0.0
            for flag in world_object.get_flags_to_set():
                self.player.set_flag(flag)
            return

    def _update_level_transition(self, dt):
        self.transition_timer += dt
        screen_width, screen_height = self.app.get_screen_size()
        self.camera.update(self.player, screen_width, screen_height)
        if self.transition_timer < TRANSITION_FADE_DURATION:
            return

        from game.scenes.splash_scene import SplashScene

        target_level = self.transition_target_level
        target_spawn = self.transition_target_spawn
        self.app.set_scene(
            SplashScene(
                self.app,
                lambda: GameScene(
                    self.app,
                    target_level,
                    player=self.player,
                    target_spawn=target_spawn,
                ),
                title=self.localizer.t("ui.common.area_loading"),
                duration=0.8,
                background=(10, 10, 16),
            )
        )

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

            attack = self.player.get_current_attack_context()
            if attack is None:
                return

            if attack.is_ranged:
                self._spawn_player_projectile(attack)
                self._player_attack_applied = True
                return

            damage = attack.damage
            attack_origin, attack_end, attack_thickness = self._get_player_attack_segment(attack)
            for enemy in self.enemies:
                if enemy.is_dead:
                    continue
                if _segment_hits_rect(attack_origin, attack_end, attack_thickness, enemy.get_hitbox_rect()):
                    if enemy.take_damage(damage):
                        self._spawn_damage_number(enemy, damage)
            self._player_attack_applied = True
            return

        self._player_attack_applied = False

    def _spawn_damage_number(self, enemy, damage):
        center = enemy.get_center()
        self.damage_numbers.append(
            DamageNumber(
                text=str(damage),
                x=center.x,
                y=enemy.position.y - 8,
            )
        )

    def _update_damage_numbers(self, dt):
        alive_numbers = []
        for damage_number in self.damage_numbers:
            damage_number.update(dt)
            if not damage_number.is_dead:
                alive_numbers.append(damage_number)
        self.damage_numbers = alive_numbers

    def _spawn_player_projectile(self, attack):
        center = self.player.get_center()
        spawn_x = center.x + attack.aim_direction.x * 16
        spawn_y = center.y + attack.aim_direction.y * 16
        self.player_projectiles.append(
            PlayerProjectile(
                spawn_x,
                spawn_y,
                attack.aim_direction.x,
                attack.aim_direction.y,
                speed=attack.projectile_speed,
                damage=attack.damage,
                radius=attack.projectile_radius,
                max_distance=attack.projectile_distance,
            )
        )

    def _update_player_projectiles(self, dt):
        alive_projectiles = []
        for projectile in self.player_projectiles:
            projectile.update(dt, self)
            if not projectile.is_dead:
                alive_projectiles.append(projectile)
        self.player_projectiles = alive_projectiles

    def _get_player_attack_segment(self, attack=None):
        center = self.player.get_center()
        attack = attack or self.player.get_current_attack_context()
        aim_source = attack.aim_direction if attack is not None else self.player.aim_direction
        attack_range = attack.range if attack is not None else 40
        attack_thickness = attack.thickness if attack is not None else 42
        aim = aim_source.normalize() if aim_source.length() > 0 else Vector2(1, 0)
        start = Vector2(center.x + aim.x * 12, center.y + aim.y * 12)
        end = Vector2(start.x + aim.x * attack_range, start.y + aim.y * attack_range)
        return start, end, attack_thickness

    def _mouse_world_position(self, mouse_pos):
        return Vector2(
            mouse_pos[0] + self.camera.position.x,
            mouse_pos[1] + self.camera.position.y,
        )

    def _read_movement_direction(self, keys):
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
        return Vector2(dx, dy)

    def draw(self):
        screen_width, _ = self.app.get_screen_size()
        self.app.screen.fill(COLORS["BLACK"])
        self.tilemap.draw(self.app.screen, self.camera)
        for world_object in self.world_objects:
            world_object.draw(self.app.screen, self.camera)
        for enemy in self.enemies:
            enemy.draw(self.app.screen, self.camera)
        self._draw_player_projectiles()
        self._draw_damage_numbers()
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
        self._draw_transition_overlay()

    def _draw_damage_numbers(self):
        for damage_number in self.damage_numbers:
            damage_number.draw(self.app.screen, self.camera, self.info_font)

    def _draw_player_projectiles(self):
        for projectile in self.player_projectiles:
            projectile.draw(self.app.screen, self.camera)

    def _draw_transition_overlay(self):
        if self.transition_target_level is None:
            return

        progress = min(1.0, self.transition_timer / TRANSITION_FADE_DURATION)
        screen_width, screen_height = self.app.get_screen_size()
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(255 * progress)))
        self.app.screen.blit(overlay, (0, 0))

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


class DamageNumber:
    def __init__(self, text, x, y):
        self.text = text
        self.position = Vector2(x, y)
        self.age = 0.0
        self.duration = DAMAGE_NUMBER_DURATION
        self.is_dead = False

    def update(self, dt):
        self.age += dt
        self.position.y -= DAMAGE_NUMBER_RISE_SPEED * dt
        if self.age >= self.duration:
            self.is_dead = True

    def draw(self, screen, camera, font):
        progress = min(1.0, self.age / self.duration)
        alpha = int(255 * (1.0 - progress))
        scale_offset = -8 * progress
        text_surface = font.render(self.text, True, (255, 235, 120))
        outline_surface = font.render(self.text, True, COLORS["BLACK"])
        text_surface.set_alpha(alpha)
        outline_surface.set_alpha(alpha)

        x = self.position.x - camera.position.x
        y = self.position.y - camera.position.y + scale_offset
        rect = text_surface.get_rect(center=(x, y))
        for offset_x, offset_y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            screen.blit(outline_surface, rect.move(offset_x, offset_y))
        screen.blit(text_surface, rect)


class PlayerProjectile:
    def __init__(self, x, y, dir_x, dir_y, speed, damage, radius=5, max_distance=520.0):
        self.position = Vector2(x, y)
        self.direction = Vector2(dir_x, dir_y).normalize() if Vector2(dir_x, dir_y).length() > 0 else Vector2(1, 0)
        self.speed = float(speed)
        self.damage = max(1, int(damage))
        self.radius = max(2, int(radius))
        self.max_distance = float(max_distance)
        self.travelled_distance = 0.0
        self.is_dead = False

    def update(self, dt, game_scene):
        if self.is_dead:
            return

        step = self.direction * (self.speed * dt)
        next_x = self.position.x + step.x
        next_y = self.position.y + step.y
        probe = _ProjectileProbe(self.radius)

        if game_scene.collision_system.check_collision(next_x - self.radius, next_y - self.radius, probe):
            self.is_dead = True
            return

        self.position.x = next_x
        self.position.y = next_y
        self.travelled_distance += step.length()

        projectile_rect = (
            self.position.x - self.radius,
            self.position.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )
        for enemy in game_scene.enemies:
            if enemy.is_dead:
                continue
            if not _rects_intersect(projectile_rect, enemy.get_hitbox_rect()):
                continue
            if enemy.take_damage(self.damage):
                game_scene._spawn_damage_number(enemy, self.damage)
            self.is_dead = True
            return

        if self.travelled_distance >= self.max_distance:
            self.is_dead = True

    def draw(self, screen, camera):
        if self.is_dead:
            return
        x = int(self.position.x - camera.position.x)
        y = int(self.position.y - camera.position.y)
        pygame.draw.circle(screen, (150, 220, 255), (x, y), self.radius)
        pygame.draw.circle(screen, COLORS["BLACK"], (x, y), self.radius, width=1)


class _ProjectileProbe:
    def __init__(self, radius):
        self.radius = radius * 2

    def get_hitbox_at(self, x, y):
        return (x, y, self.radius, self.radius)
