import math
import random
from datetime import datetime, timezone
from pathlib import Path

import pygame

from game.core.camera import Camera
from game.core.vector import Vector2
from game.effects import DamageNumber
from game.entities.enemies import BeetleEnemy, EnemyManager, ForestGuardianBoss, MeleeEnemy, RangedEnemy, SpiderEnemy
from game.entities.projectiles import PlayerProjectile
from game.entities.player import Player
from game.items import create_item_stack
from game.localization import get_localizer
from game.objects import create_world_object
from game.quests import QuestManager
from game.save_system import SAVE_VERSION, load_player_state, serialize_player_state
from game.scenes.base import Scene
from game.ui.hud import HUD
from game.world.collision import CollisionSystem
from game.world.level import load_level
from game.world.tilemap import TileMap
from settings import (
    COLORS,
    LEVELS_DIR,
    RENDER_CULL_MARGIN,
)


TRANSITION_FADE_DURATION = 0.45
CHARGED_ATTACK_THRESHOLD = 1.5
HIT_STOP_DURATION = 0.055
SCREEN_SHAKE_DURATION = 0.12
SCREEN_SHAKE_STRENGTH = 5.0
CHECKPOINT_XP_REWARD = 12
TRANSITION_XP_REWARD = 18


class GameScene(Scene):
    def __init__(self, app, level_path, player=None, target_spawn=None, save_data=None):
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
            tileset=self.level.tileset,
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
            if save_data is not None:
                load_player_state(self.player, save_data.get("player", {}))
                self.player.position = Vector2(
                    self.player.spawn_position.x,
                    self.player.spawn_position.y,
                )
        else:
            self.player = player
            if target_spawn is not None:
                self.player.move_to_spawn(spawn_world_x, spawn_world_y)
        self.world_objects, enemies = self._load_world_objects()
        self._apply_level_state()
        defeated_enemy_ids = getattr(self, "_pending_defeated_enemy_ids", set())
        if defeated_enemy_ids:
            enemies = [
                enemy for enemy in enemies
                if getattr(enemy, "persistence_id", "") not in defeated_enemy_ids
            ]
        self.enemy_manager = EnemyManager(self, enemies)
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
        self.jump_pressed_last_frame = False
        self.jump_requested = False
        self.hit_stop_timer = 0.0
        self.screen_shake_timer = 0.0
        self.screen_shake_strength = 0.0

        world_width = self.tilemap.width * self.tilemap.tile_size
        world_height = self.tilemap.height * self.tilemap.tile_size
        self.camera = Camera(world_width, world_height)
        self.hud = HUD()
        self.quest_manager = QuestManager(self.player)
        self.info_font = pygame.font.Font(None, 28)
        self.interaction_font = pygame.font.Font(None, 30)
        self.last_interaction_message = ""
        self.last_interaction_timer = 0.0
        self.current_interaction_target = None
        self.active_checkpoint_contacts = set()
        self.save_indicator_timer = 0.0
        self.save_progress(reason="scene_enter")

    @property
    def enemies(self):
        """Compatibility view for combat and projectile code."""
        return self.enemy_manager.enemies

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

    def save_progress(self, reason="manual", checkpoint_name=None):
        slot = self.app.save_manager.get_active_slot_meta()
        if slot is None:
            return False

        snapshot = self._build_save_snapshot(reason=reason, checkpoint_name=checkpoint_name)
        save_success = self.app.save_manager.save_slot(slot.slot_id, snapshot, title=slot.title)
        if save_success:
            self.save_indicator_timer = 1.6
        return save_success

    def _build_save_snapshot(self, reason="manual", checkpoint_name=None):
        active_slot = self.app.save_manager.get_active_slot_meta()
        return {
            "version": SAVE_VERSION,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "current_level": self.level_key,
            "player": serialize_player_state(self.player),
            "meta": {
                "reason": str(reason),
                "last_checkpoint_name": checkpoint_name or (
                    active_slot.last_checkpoint_name if active_slot is not None else None
                ),
            },
        }

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
            if object_type == "enemy_spider":
                enemies.append(self._create_enemy(raw_object, SpiderEnemy))
                continue
            if object_type == "enemy_beetle":
                enemies.append(self._create_enemy(raw_object, BeetleEnemy))
                continue
            if object_type in {"enemy_boss_forest_guardian", "boss_forest_guardian", "enemy_boss_deer"}:
                enemies.append(self._create_enemy(raw_object, ForestGuardianBoss))
                continue

            world_object = create_world_object(raw_object, self.level.tile_size)
            if world_object is not None:
                if getattr(world_object, "is_container", False):
                    object_id = world_object.get_persistence_id()
                    world_object.bind_state_store(
                        self.player.container_states,
                        f"{self.level_key}:{object_id}",
                    )
                world_objects.append(world_object)
        return world_objects, enemies

    def _get_level_state(self, create=True):
        if not create:
            return self.player.level_states.get(self.level_key)

        state = self.player.level_states.setdefault(
            self.level_key,
            {
                "picked_object_ids": set(),
                "depleted_object_ids": set(),
                "activated_checkpoint_ids": set(),
                "defeated_enemy_ids": set(),
                "active_checkpoint_id": None,
            },
        )
        state.setdefault("picked_object_ids", set())
        state.setdefault("depleted_object_ids", set())
        state.setdefault("activated_checkpoint_ids", set())
        state.setdefault("defeated_enemy_ids", set())
        state.setdefault("active_checkpoint_id", None)
        return state

    def _apply_level_state(self):
        level_state = self._get_level_state(create=False)
        if not level_state:
            return

        picked_ids = level_state.get("picked_object_ids", set())
        depleted_ids = level_state.get("depleted_object_ids", set())
        activated_checkpoint_ids = level_state.get("activated_checkpoint_ids", set())
        defeated_enemy_ids = level_state.get("defeated_enemy_ids", set())

        filtered_objects = []
        for world_object in self.world_objects:
            persistence_id = world_object.get_persistence_id()
            if persistence_id in picked_ids and hasattr(world_object, "is_picked"):
                continue
            if persistence_id in depleted_ids and getattr(world_object, "is_gatherable", False):
                world_object.restore_depleted_state()
            if persistence_id in activated_checkpoint_ids and getattr(world_object, "is_checkpoint", False):
                world_object.restore_activated_state()
            filtered_objects.append(world_object)
        self.world_objects = filtered_objects
        self.collision_system.set_objects(self.world_objects)

        self.player.container_states = {
            key: value
            for key, value in self.player.container_states.items()
            if isinstance(key, str)
        }
        self._rebind_container_state()

        self._apply_enemy_level_state(defeated_enemy_ids)

    def _apply_enemy_level_state(self, defeated_enemy_ids):
        if not defeated_enemy_ids:
            return
        self._pending_defeated_enemy_ids = set(defeated_enemy_ids)

    def _rebind_container_state(self):
        for world_object in self.world_objects:
            if not getattr(world_object, "is_container", False):
                continue
            object_id = world_object.get_persistence_id()
            world_object.bind_state_store(
                self.player.container_states,
                f"{self.level_key}:{object_id}",
            )

    def _create_enemy(self, raw_object, enemy_class):
        width = raw_object.get("width", 1) * self.level.tile_size
        height = raw_object.get("height", 1) * self.level.tile_size
        x = raw_object.get("x", 0) * self.level.tile_size
        y = raw_object.get("y", 0) * self.level.tile_size
        properties = raw_object.get("properties", {})

        enemy = enemy_class(
            x,
            y,
            width,
            height,
            name=raw_object.get("name", enemy_class.__name__),
            max_health=int(properties.get("health", raw_object.get("health", 20))),
            speed=int(properties.get("speed", raw_object.get("speed", 80))),
            damage=int(properties.get("damage", raw_object.get("damage", 4))),
            xp_reward=int(properties.get("xp_reward", raw_object.get("xp_reward", 10))),
            **self._enemy_resistance_kwargs(properties),
            **self._enemy_common_kwargs(raw_object, properties),
            **self._enemy_hitbox_kwargs(properties),
            **self._enemy_specific_kwargs(raw_object, enemy_class),
        )
        enemy.persistence_id = self._build_enemy_persistence_id(raw_object, enemy_class)
        return enemy

    def _build_enemy_persistence_id(self, raw_object, enemy_class):
        object_id = raw_object.get("id")
        if object_id is not None:
            return str(object_id)
        return (
            f"{enemy_class.__name__.lower()}:"
            f"{raw_object.get('name', enemy_class.__name__).lower()}:"
            f"{int(raw_object.get('x', 0))}:{int(raw_object.get('y', 0))}"
        )

    def _enemy_common_kwargs(self, raw_object, properties):
        result = {
            "scale": float(properties.get("scale", raw_object.get("scale", 1.0))),
            "sprite_scale": float(properties.get("sprite_scale", raw_object.get("sprite_scale", 1.0))),
            "sprite_offset_x": float(properties.get("sprite_offset_x", raw_object.get("sprite_offset_x", 0))),
            "sprite_offset_y": float(properties.get("sprite_offset_y", raw_object.get("sprite_offset_y", 0))),
            "stationary": bool(properties.get("stationary", raw_object.get("stationary", False))),
        }
        if "patrol_radius" in properties or "patrol_radius" in raw_object:
            result["patrol_radius"] = int(properties.get("patrol_radius", raw_object.get("patrol_radius", 140)))
        if "patrol_idle_min" in properties or "patrol_idle_min" in raw_object:
            result["patrol_idle_min"] = float(properties.get("patrol_idle_min", raw_object.get("patrol_idle_min", 0.45)))
        if "patrol_idle_max" in properties or "patrol_idle_max" in raw_object:
            result["patrol_idle_max"] = float(properties.get("patrol_idle_max", raw_object.get("patrol_idle_max", 1.1)))
        if "linger_duration" in properties or "linger_duration" in raw_object:
            result["linger_duration"] = float(properties.get("linger_duration", raw_object.get("linger_duration", 1.0)))
        return result

    def _enemy_resistance_kwargs(self, properties):
        raw_resistances = properties.get("resistances")
        if not isinstance(raw_resistances, dict) or not raw_resistances:
            return {}
        return {"resistances": raw_resistances}

    def _enemy_hitbox_kwargs(self, properties):
        result = {}
        body = properties.get("body_hitbox") or {}
        hurt = properties.get("hurtbox") or {}
        attack = properties.get("attack_hitbox") or {}
        collision_circle = properties.get("collision_circle") or {}

        if body:
            if "width" in body:
                result["hitbox_width"] = float(body["width"])
            if "height" in body:
                result["hitbox_height"] = float(body["height"])
            if "offset_x" in body:
                result["hitbox_offset_x"] = float(body["offset_x"])
            if "offset_y" in body:
                result["hitbox_offset_y"] = float(body["offset_y"])

        if hurt:
            if "width" in hurt:
                result["hurtbox_width"] = float(hurt["width"])
            if "height" in hurt:
                result["hurtbox_height"] = float(hurt["height"])
            if "offset_x" in hurt:
                result["hurtbox_offset_x"] = float(hurt["offset_x"])
            if "offset_y" in hurt:
                result["hurtbox_offset_y"] = float(hurt["offset_y"])

        if attack:
            if "width" in attack:
                result["attack_hitbox_width"] = float(attack["width"])
            if "height" in attack:
                result["attack_hitbox_height"] = float(attack["height"])
            if "offset_x" in attack:
                result["attack_hitbox_offset_x"] = float(attack["offset_x"])
            if "offset_y" in attack:
                result["attack_hitbox_offset_y"] = float(attack["offset_y"])
            if "mirror_with_facing" in attack:
                result["attack_hitbox_mirror_with_facing"] = bool(attack["mirror_with_facing"])

        if collision_circle:
            if "radius" in collision_circle:
                result["collision_circle_radius"] = float(collision_circle["radius"])
            if "offset_x" in collision_circle:
                result["collision_circle_offset_x"] = float(collision_circle["offset_x"])
            if "offset_y" in collision_circle:
                result["collision_circle_offset_y"] = float(collision_circle["offset_y"])
        return result

    def _enemy_specific_kwargs(self, raw_object, enemy_class):
        properties = raw_object.get("properties", {})
        if enemy_class is MeleeEnemy:
            return {
                "melee_range": int(properties.get("melee_range", raw_object.get("melee_range", 44))),
                "attack_cooldown": float(properties.get("attack_cooldown", raw_object.get("attack_cooldown", 1.0))),
            }
        if enemy_class is ForestGuardianBoss:
            return {
                "melee_range": int(properties.get("melee_range", raw_object.get("melee_range", 66))),
                "charge_range": int(properties.get("charge_range", raw_object.get("charge_range", 240))),
                "charge_speed": int(properties.get("charge_speed", raw_object.get("charge_speed", 300))),
                "attack_cooldown": float(properties.get("attack_cooldown", raw_object.get("attack_cooldown", 1.0))),
                "detection_radius": int(properties.get("detection_radius", raw_object.get("detection_radius", 420))),
            }
        if enemy_class is SpiderEnemy:
            return {
                "melee_range": int(properties.get("melee_range", raw_object.get("melee_range", 24))),
                "leap_range": int(properties.get("leap_range", raw_object.get("leap_range", 150))),
                "leap_min_range": int(properties.get("leap_min_range", raw_object.get("leap_min_range", 64))),
                "leap_speed": int(properties.get("leap_speed", raw_object.get("leap_speed", 360))),
                "leap_duration": float(properties.get("leap_duration", raw_object.get("leap_duration", 0.28))),
                "spit_range": int(properties.get("spit_range", raw_object.get("spit_range", 250))),
                "projectile_speed": int(properties.get("projectile_speed", raw_object.get("projectile_speed", 290))),
                "projectile_radius": int(properties.get("projectile_radius", raw_object.get("projectile_radius", 6))),
                "slow_amount": float(properties.get("slow_amount", raw_object.get("slow_amount", 0.22))),
                "slow_duration": float(properties.get("slow_duration", raw_object.get("slow_duration", 2.6))),
                "attack_cooldown": float(properties.get("attack_cooldown", raw_object.get("attack_cooldown", 1.1))),
                "detection_radius": int(properties.get("detection_radius", raw_object.get("detection_radius", 260))),
            }
        if enemy_class is BeetleEnemy:
            return {
                "melee_range": int(properties.get("melee_range", raw_object.get("melee_range", 26))),
                "charge_range": int(properties.get("charge_range", raw_object.get("charge_range", 210))),
                "charge_min_range": int(properties.get("charge_min_range", raw_object.get("charge_min_range", 70))),
                "charge_speed": int(properties.get("charge_speed", raw_object.get("charge_speed", 260))),
                "charge_duration": float(properties.get("charge_duration", raw_object.get("charge_duration", 0.5))),
                "shell_duration": float(properties.get("shell_duration", raw_object.get("shell_duration", 2.4))),
                "shell_cooldown": float(properties.get("shell_cooldown", raw_object.get("shell_cooldown", 7.5))),
                "shell_regen_per_second": float(
                    properties.get("shell_regen_per_second", raw_object.get("shell_regen_per_second", 4.5))
                ),
                "shell_trigger_health_ratio": float(
                    properties.get("shell_trigger_health_ratio", raw_object.get("shell_trigger_health_ratio", 0.45))
                ),
                "shell_damage_multiplier": float(
                    properties.get("shell_damage_multiplier", raw_object.get("shell_damage_multiplier", 0.35))
                ),
                "attack_cooldown": float(properties.get("attack_cooldown", raw_object.get("attack_cooldown", 1.0))),
                "detection_radius": int(properties.get("detection_radius", raw_object.get("detection_radius", 230))),
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

    def open_container(self, container):
        from game.scenes.container_inventory_scene import ContainerInventoryScene

        self.app.set_scene(ContainerInventoryScene(self.app, self, container))

    def open_map(self):
        from game.scenes.map_scene import MapScene

        self.app.set_scene(MapScene(self.app, self))

    def open_crafting(self):
        from game.scenes.crafting_scene import CraftingScene

        self.app.set_scene(CraftingScene(self.app, self))

    def open_progression(self):
        from game.scenes.progression_scene import ProgressionScene

        self.app.set_scene(ProgressionScene(self.app, self))

    def open_quest_log(self):
        from game.scenes.quest_log_scene import QuestLogScene

        self.app.set_scene(QuestLogScene(self.app, self))

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
                elif event.key == pygame.K_o:
                    self.open_progression()
                elif event.key == pygame.K_j:
                    self.open_quest_log()
                elif event.key == pygame.K_e:
                    self.try_interact()
                elif event.key == pygame.K_f:
                    stack = self.player.get_hotbar_stack(self.player.selected_hotbar_index)
                    item_name = stack.name if stack is not None else ""
                    if self.player.use_selected_hotbar_item():
                        self.last_interaction_message = self.localizer.t("ui.consumables.used", name=item_name)
                    else:
                        self.last_interaction_message = self.localizer.t("ui.consumables.cannot_use")
                    self.last_interaction_timer = 1.5
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    self.player.select_hotbar_slot(event.key - pygame.K_1)
                elif event.key == pygame.K_SPACE and not self.player.is_jumping:
                    self.jump_requested = True
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
                if not self.player.attack_towards(target.x, target.y, attack_kind=attack_kind):
                    self._handle_attack_fail()
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
        self.mark_object_picked(pickable_object)

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
        if getattr(target, "is_gatherable", False) and getattr(target, "is_depleted", False):
            self.mark_object_depleted(target)
        if result and getattr(target, "is_picked", False):
            self.world_objects = [obj for obj in self.world_objects if obj is not target]
            self.collision_system.set_objects(self.world_objects)
        return result

    def mark_object_picked(self, world_object):
        if getattr(world_object, "auto_pickup", False):
            return
        level_state = self._get_level_state()
        level_state["picked_object_ids"].add(world_object.get_persistence_id())

    def mark_object_depleted(self, world_object):
        level_state = self._get_level_state()
        level_state["depleted_object_ids"].add(world_object.get_persistence_id())

    def mark_checkpoint_activated(self, checkpoint_object):
        checkpoint_id = checkpoint_object.get_persistence_id()
        level_state = self._get_level_state()
        level_state["activated_checkpoint_ids"].add(checkpoint_id)
        level_state["active_checkpoint_id"] = checkpoint_id

    def mark_enemy_defeated(self, enemy):
        persistence_id = getattr(enemy, "persistence_id", None)
        if not persistence_id:
            return
        level_state = self._get_level_state()
        level_state["defeated_enemy_ids"].add(str(persistence_id))

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

        self._update_screen_shake(dt)
        if self.hit_stop_timer > 0:
            self.hit_stop_timer = max(0.0, self.hit_stop_timer - dt)
            self._update_damage_numbers(dt)
            if self.last_interaction_timer > 0:
                self.last_interaction_timer = max(0.0, self.last_interaction_timer - dt)
                if self.last_interaction_timer == 0.0:
                    self.last_interaction_message = ""
            return

        keys = pygame.key.get_pressed()
        charged_threshold = CHARGED_ATTACK_THRESHOLD * self.player.get_charge_time_multiplier()
        if self.mouse_buttons_held == {1, 3}:
            self.mouse_hold_time += dt
            if not self.charged_combo_fired and self.mouse_hold_time >= charged_threshold:
                mouse_pos = pygame.mouse.get_pos()
                target = self._mouse_world_position(mouse_pos)
                if self.player.attack_towards(target.x, target.y, attack_kind="charged"):
                    self.charged_combo_fired = True
                else:
                    self._handle_attack_fail()
        else:
            self.mouse_hold_time = 0.0
            self.charged_combo_fired = False
        jump_pressed = self._is_jump_pressed(keys)
        if jump_pressed and not self.jump_pressed_last_frame and not self.player.is_jumping:
            self.jump_requested = True
        self.jump_pressed_last_frame = jump_pressed
        self.player.update(dt, keys, self)
        if self.jump_requested and not self.player.is_jumping:
            direction = self._resolve_jump_direction(keys)
            if direction.length() > 0:
                self.player.try_jump(direction, self)
        self.jump_requested = False
        self._update_world_objects(dt)
        self._update_map_reveal()
        self._update_grass_hide_zones()
        self._update_checkpoints()
        self.enemy_manager.update(dt)
        self._update_auto_pickups()
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
        if self.save_indicator_timer > 0:
            self.save_indicator_timer = max(0.0, self.save_indicator_timer - dt)

    def _update_checkpoints(self):
        checkpoint_contacts = set()
        for world_object in self.world_objects:
            if not getattr(world_object, "is_checkpoint", False):
                continue
            checkpoint_id = world_object.get_persistence_id()
            if not world_object.can_activate(self.player):
                continue
            checkpoint_contacts.add(checkpoint_id)
            if checkpoint_id in self.active_checkpoint_contacts:
                continue
            activated, is_new_activation = world_object.activate(self.player, self)
            if not activated:
                continue
            self.mark_checkpoint_activated(world_object)
            checkpoint_key = (
                f"checkpoint:{self.level_key}:{int(world_object.position.x)}:{int(world_object.position.y)}"
            )
            self._award_player_xp(CHECKPOINT_XP_REWARD, checkpoint_key, append=True)
            save_success = self.save_progress(reason="checkpoint", checkpoint_name=world_object.name)
            if is_new_activation:
                message_key = "ui.saves.checkpoint_saved" if save_success else "ui.saves.checkpoint_failed"
                self.last_interaction_message = self.localizer.t(message_key, name=world_object.name)
                self.last_interaction_timer = 1.5
        self.active_checkpoint_contacts = checkpoint_contacts

    def _update_world_objects(self, dt):
        for world_object in self.world_objects:
            world_object.update(dt, self)

    def _update_auto_pickups(self):
        player_hitbox = self.player.get_hitbox_rect()
        picked_objects = []
        for world_object in self.world_objects:
            if not getattr(world_object, "auto_pickup", False):
                continue
            if getattr(world_object, "is_picked", False):
                continue
            if not _rects_intersect(player_hitbox, world_object.get_hitbox_rect()):
                continue
            if self.try_pickup_object(world_object):
                picked_objects.append(world_object)

        if not picked_objects:
            return
        picked_set = set(picked_objects)
        self.world_objects = [obj for obj in self.world_objects if obj not in picked_set]
        self.collision_system.set_objects(self.world_objects)

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
            transition_key = (
                f"transition:{self.level_key}:{int(world_object.position.x)}:{int(world_object.position.y)}:{target_level}"
            )
            self._award_player_xp(TRANSITION_XP_REWARD, transition_key, append=True)
            for flag in world_object.get_flags_to_set():
                self.player.set_flag(flag)
            self.save_progress(reason="transition")
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

    def _camera_world_rect(self, margin=0):
        screen_width, screen_height = self.app.get_screen_size()
        return pygame.Rect(
            int(self.camera.position.x - margin),
            int(self.camera.position.y - margin),
            int(screen_width + margin * 2),
            int(screen_height + margin * 2),
        )

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
                if not self._attack_hits_enemy(attack, attack_origin, attack_end, attack_thickness, enemy):
                    continue
                if enemy.take_damage(damage, attack.kind):
                    enemy.apply_hit_reaction(attack.aim_direction, attack.knockback, attack.stagger)
                    self._spawn_damage_number(enemy, enemy.last_damage_taken)
                    self._trigger_hit_feedback(attack)
            self._player_attack_applied = True
            return

        self._player_attack_applied = False

    def _attack_hits_enemy(self, attack, attack_origin, attack_end, attack_thickness, enemy):
        if attack.shape == "arc":
            return _arc_hits_rect(
                attack_origin,
                attack.aim_direction,
                attack.range,
                attack.arc_degrees,
                enemy.get_hurtbox_rect(),
            )
        return _segment_hits_rect(attack_origin, attack_end, attack_thickness, enemy.get_hurtbox_rect())

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
        sprite_scale = 1.0
        if attack.kind == "heavy":
            sprite_scale = 1.35
        elif attack.kind == "charged":
            sprite_scale = 1.55
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
                sprite_scale=sprite_scale,
                source_x=center.x,
                source_y=center.y,
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

    def _handle_attack_fail(self):
        if self.player.last_attack_fail_reason == "not_enough_stamina":
            self.last_interaction_message = self.localizer.t("ui.combat.no_stamina")
            self.last_interaction_timer = 0.7

    def _trigger_hit_feedback(self, attack):
        self.hit_stop_timer = max(self.hit_stop_timer, HIT_STOP_DURATION)
        strength_scale = {"light": 0.8, "heavy": 1.0, "charged": 1.35}.get(attack.kind, 0.8)
        self.screen_shake_timer = max(self.screen_shake_timer, SCREEN_SHAKE_DURATION)
        self.screen_shake_strength = max(self.screen_shake_strength, SCREEN_SHAKE_STRENGTH * strength_scale)

    def _update_screen_shake(self, dt):
        if self.screen_shake_timer <= 0:
            self.screen_shake_timer = 0.0
            self.screen_shake_strength = 0.0
            return
        self.screen_shake_timer = max(0.0, self.screen_shake_timer - dt)
        if self.screen_shake_timer == 0.0:
            self.screen_shake_strength = 0.0

    def _current_screen_shake_offset(self):
        if self.screen_shake_timer <= 0 or self.screen_shake_strength <= 0:
            return Vector2(0, 0)
        progress = self.screen_shake_timer / SCREEN_SHAKE_DURATION
        strength = self.screen_shake_strength * progress
        return Vector2(
            random.uniform(-strength, strength),
            random.uniform(-strength, strength),
        )

    def _build_hud_combat_state(self):
        weapon = self.player.get_equipped_weapon()
        charge_progress = 0.0
        charging = self.mouse_buttons_held == {1, 3} and not self.charged_combo_fired
        charged_threshold = CHARGED_ATTACK_THRESHOLD * self.player.get_charge_time_multiplier()
        if charging:
            charge_progress = min(1.0, self.mouse_hold_time / max(0.001, charged_threshold))
        return {
            "charging": charging,
            "charge_progress": charge_progress,
            "weapon_name": weapon.name if weapon is not None else self.localizer.t("ui.combat.unarmed"),
            "weapon_class": weapon.definition.weapon_class if weapon is not None else None,
            "not_enough_stamina": self.player.last_attack_fail_reason == "not_enough_stamina" and self.last_interaction_timer > 0,
        }

    def _award_player_xp(self, amount, source_key=None, append=False):
        result = self.player.add_experience(amount, source_key=source_key)
        if result["gained"] <= 0:
            return False

        message = self.localizer.t("ui.progression.xp_gained", amount=result["gained"])
        if result["level_ups"] > 0:
            level_message = self.localizer.t(
                "ui.progression.level_up",
                level=self.player.level,
                points=self.player.skill_points,
            )
            message = f"{message} | {level_message}"

        if append and self.last_interaction_message:
            self.last_interaction_message = f"{self.last_interaction_message} | {message}"
        else:
            self.last_interaction_message = message
        self.last_interaction_timer = max(self.last_interaction_timer, 1.8)
        return True

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

    def _is_jump_pressed(self, keys):
        return keys[pygame.K_SPACE]

    def _resolve_jump_direction(self, keys):
        direction = self._read_movement_direction(keys)
        if direction.length() > 0:
            return direction.normalize()
        if self.player.last_movement_input.length() > 0:
            return self.player.last_movement_input.normalize()
        if self.player.animation_motion.length() > 0.01:
            return self.player.animation_motion.normalize()
        if self.player.direction.length() > 0:
            return self.player.direction.normalize()
        return Vector2()

    def draw(self):
        screen_width, _ = self.app.get_screen_size()
        self.app.screen.fill(COLORS["BLACK"])
        shake_offset = self._current_screen_shake_offset()
        self.camera.position.x += shake_offset.x
        self.camera.position.y += shake_offset.y
        visible_rect = self._camera_world_rect(RENDER_CULL_MARGIN)
        self.tilemap.draw(self.app.screen, self.camera)
        overlay_world_objects = []
        for world_object in self.world_objects:
            if not visible_rect.colliderect(world_object.get_hitbox_rect()):
                continue
            if getattr(world_object, "is_grass_hide_zone", False):
                overlay_world_objects.append(world_object)
                continue
            world_object.draw(self.app.screen, self.camera)
        self.enemy_manager.draw(self.app.screen, self.camera)
        self._draw_player_projectiles()
        self._draw_damage_numbers()
        self.player.draw(self.app.screen, self.camera)
        for world_object in overlay_world_objects:
            world_object.draw(self.app.screen, self.camera)
        self.camera.position.x -= shake_offset.x
        self.camera.position.y -= shake_offset.y
        self.hud.draw(
            self.app.screen,
            self.player,
            quest_manager=self.quest_manager,
            combat_state=self._build_hud_combat_state(),
            fps=self.app.current_fps,
            show_fps=self.app.show_fps,
            save_indicator_alpha=self._save_indicator_alpha(),
        )
        if self.current_interaction_target is not None:
            self._draw_interaction_prompt(self.current_interaction_target)
        if self.last_interaction_message:
            message = self.info_font.render(self.last_interaction_message, True, COLORS["WHITE"])
            self.app.screen.blit(
                message,
                message.get_rect(center=(screen_width // 2, 24)),
            )
        self._draw_transition_overlay()

    def _save_indicator_alpha(self):
        if self.save_indicator_timer <= 0:
            return 0
        return int(255 * min(1.0, self.save_indicator_timer / 0.35))

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


def _arc_hits_rect(origin, aim_direction, radius, arc_degrees, rect):
    rx, ry, rw, rh = rect
    center = Vector2(rx + rw / 2, ry + rh / 2)
    to_target = Vector2(center.x - origin.x, center.y - origin.y)
    distance = to_target.length()
    if distance > radius + max(rw, rh) * 0.5:
        return False
    if distance == 0:
        return True
    aim = aim_direction.normalize() if aim_direction.length() > 0 else Vector2(1, 0)
    direction = to_target.normalize()
    dot = max(-1.0, min(1.0, aim.x * direction.x + aim.y * direction.y))
    angle = math.degrees(math.acos(dot))
    return angle <= arc_degrees / 2
