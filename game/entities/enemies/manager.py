import pygame

from game.objects import PickableObject
from settings import (
    ENEMY_BACKGROUND_UPDATE_INTERVAL,
    ENEMY_BACKGROUND_UPDATE_MARGIN,
    ENEMY_FULL_UPDATE_MARGIN,
    RENDER_CULL_MARGIN,
)


class EnemyManager:
    """Owns enemy lifecycle, background simulation, and camera culling."""

    def __init__(self, game_scene, enemies=None):
        self.game_scene = game_scene
        self.enemies = list(enemies or ())

    def update(self, dt):
        alive_enemies = []
        full_update_rect = self.game_scene._camera_world_rect(ENEMY_FULL_UPDATE_MARGIN)
        background_update_rect = self.game_scene._camera_world_rect(ENEMY_BACKGROUND_UPDATE_MARGIN)

        for enemy in self.enemies:
            self._update_enemy(enemy, dt, full_update_rect, background_update_rect)
            if enemy.is_dead:
                self._handle_enemy_death(enemy)
                if not getattr(enemy, "ready_for_removal", True):
                    alive_enemies.append(enemy)
                continue
            alive_enemies.append(enemy)

        self.enemies = alive_enemies

    def draw(self, screen, camera):
        visible_rect = self.game_scene._camera_world_rect(RENDER_CULL_MARGIN)
        for enemy in self.enemies:
            if self._is_visible(enemy, visible_rect):
                if enemy.is_dead:
                    enemy.draw_death(screen, camera)
                else:
                    enemy.draw(screen, camera)

    def _update_enemy(self, enemy, dt, full_update_rect, background_update_rect):
        if enemy.is_dead:
            enemy.update_death_animation(dt)
            return
        if self._needs_full_update(enemy, full_update_rect):
            accumulated_dt = min(
                enemy.background_update_accumulator + dt,
                ENEMY_BACKGROUND_UPDATE_INTERVAL,
            )
            enemy.background_update_accumulator = 0.0
            enemy.update(accumulated_dt, self.game_scene)
            return

        if background_update_rect.colliderect(enemy.get_hitbox_rect()):
            enemy.background_update_accumulator += dt
            if enemy.background_update_accumulator >= ENEMY_BACKGROUND_UPDATE_INTERVAL:
                accumulated_dt = min(
                    enemy.background_update_accumulator,
                    ENEMY_BACKGROUND_UPDATE_INTERVAL,
                )
                enemy.background_update_accumulator = 0.0
                enemy.update(accumulated_dt, self.game_scene)
            return

        enemy.background_update_accumulator = min(
            enemy.background_update_accumulator + dt,
            ENEMY_BACKGROUND_UPDATE_INTERVAL,
        )

    def _needs_full_update(self, enemy, full_update_rect):
        if full_update_rect.colliderect(enemy.get_hitbox_rect()):
            return True
        if getattr(enemy, "encounter_started", False):
            return True
        if getattr(enemy, "behavior_state", None) in {"chase", "linger"}:
            return True
        return bool(getattr(enemy, "projectiles", ()))

    def _is_visible(self, enemy, visible_rect):
        if visible_rect.colliderect(enemy.get_hitbox_rect()):
            return True
        for projectile in getattr(enemy, "projectiles", ()):
            if projectile.is_dead:
                continue
            radius = max(1, int(getattr(projectile, "radius", 1)))
            projectile_rect = pygame.Rect(
                int(projectile.position.x - radius),
                int(projectile.position.y - radius),
                radius * 2,
                radius * 2,
            )
            if visible_rect.colliderect(projectile_rect):
                return True
        return False

    def _handle_enemy_death(self, enemy):
        self.game_scene.mark_enemy_defeated(enemy)
        self._spawn_drops(enemy)
        defeat_flag = getattr(enemy, "defeat_flag", None)
        if defeat_flag:
            self.game_scene.player.set_flag(defeat_flag)
        if not enemy.xp_awarded and enemy.xp_reward > 0:
            enemy.xp_awarded = True
            self.game_scene._award_player_xp(enemy.xp_reward, append=True)

    def _spawn_drops(self, enemy):
        if getattr(enemy, "loot_dropped", False):
            return
        enemy.loot_dropped = True
        drops = enemy.roll_loot() if hasattr(enemy, "roll_loot") else []
        if not drops:
            return

        scene = self.game_scene
        tile_size = max(12, int(scene.level.tile_size * 0.6))
        center = enemy.get_center()
        start_x = center.x - tile_size / 2
        start_y = center.y - tile_size / 2
        for index, drop in enumerate(drops):
            offset_x = (index % 2) * (tile_size + 4) - (tile_size + 4) / 2
            offset_y = (index // 2) * (tile_size + 4) - (tile_size + 4) / 2
            properties = {}
            if "item_id" in drop:
                properties["item_id"] = drop["item_id"]
                properties["quantity"] = int(drop.get("quantity", 1))
            if "coins" in drop:
                properties["coins"] = int(drop.get("coins", 0))
            if "knowledge_shards" in drop:
                properties["knowledge_shards"] = int(drop.get("knowledge_shards", 0))
            if not properties:
                continue
            scene.world_objects.append(
                PickableObject(
                    start_x + offset_x,
                    start_y + offset_y,
                    tile_size,
                    tile_size,
                    name=properties.get("item_id", "enemy_drop"),
                    properties={**properties, "auto_pickup": True},
                )
            )
        scene.collision_system.set_objects(scene.world_objects)
