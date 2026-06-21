from __future__ import annotations

from game.core.vector import Vector2
from game.entities.enemies.ai.states import CHASE
from game.entities.enemies.ai.steering import entity_distance
from game.entities.enemies.base import Enemy
from game.entities.enemies.projectiles import RangedProjectile


class ArcherEnemy(Enemy):
    BODY_HITBOX = {
        "width": 20,
        "height": 20,
        "offset_x": 6,
        "offset_y": 11,
    }
    HURTBOX = {
        "width": 18,
        "height": 20,
        "offset_x": 7,
        "offset_y": 10,
    }
    ATTACK_HITBOX = {
        "width": 16,
        "height": 14,
        "offset_x": 18,
        "offset_y": 13,
        "mirror_with_facing": True,
    }
    COLLISION_CIRCLE = {
        "radius": 10,
    }
    LOOT_TABLE = (
        {"item_id": "feather", "min_quantity": 1, "max_quantity": 2, "chance": 0.7},
        {"item_id": "stick", "min_quantity": 1, "max_quantity": 1, "chance": 0.4},
        {"coins": 3, "chance": 0.55},
    )

    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="ranged_enemy",
        max_health=14,
        speed=60,
        damage=4,
        preferred_distance=180,
        min_distance=120,
        attack_range=260,
        detection_radius=280,
        projectile_speed=260,
        projectile_radius=5,
        attack_cooldown=1.4,
        patrol_radius=160,
        patrol_idle_min=0.45,
        patrol_idle_max=1.1,
        linger_duration=1.0,
        xp_reward=10,
        **hitbox_kwargs,
    ):
        super().__init__(
            x,
            y,
            width,
            height,
            name=name,
            max_health=max_health,
            speed=speed,
            damage=damage,
            attack_cooldown=attack_cooldown,
            detection_radius=detection_radius,
            patrol_radius=patrol_radius,
            patrol_idle_min=patrol_idle_min,
            patrol_idle_max=patrol_idle_max,
            linger_duration=linger_duration,
            color=(200, 35, 35),
            xp_reward=xp_reward,
            **hitbox_kwargs,
        )
        self.preferred_distance = float(preferred_distance)
        self.min_distance = float(min_distance)
        self.attack_range = float(attack_range)
        self.attack_radius = self.attack_range
        self.projectile_speed = float(projectile_speed)
        self.projectile_radius = int(projectile_radius)
        self.projectiles = []

    def update(self, dt, game_scene):
        super().update(dt, game_scene)
        if self.is_dead:
            return
        if self.behavior_state != CHASE:
            self._update_projectiles(dt, game_scene)
            return
        player = game_scene.player
        player_center = player.get_center()
        distance = entity_distance(self, player)
        if distance > self.preferred_distance:
            previous_position = Vector2(self.position.x, self.position.y)
            self._move_towards(player_center.x, player_center.y, dt, game_scene, use_pathfinding=True)
            self._update_stuck_state(dt, previous_position, game_scene)
        elif distance < self.min_distance:
            previous_position = Vector2(self.position.x, self.position.y)
            self._move_away_from(player_center.x, player_center.y, dt, game_scene)
            self._update_stuck_state(dt, previous_position, game_scene)
        if distance <= self.attack_range and not self.attack_cooldown.is_active():
            self._shoot(player_center.x, player_center.y)
            self.attack_cooldown.start()
        self._update_projectiles(dt, game_scene)

    def _shoot(self, target_x, target_y):
        origin = self.get_center()
        self.projectiles.append(
            RangedProjectile(origin.x, origin.y, target_x, target_y, self.projectile_speed, self.damage, self.projectile_radius)
        )

    def _update_projectiles(self, dt, game_scene):
        alive_projectiles = []
        for projectile in self.projectiles:
            projectile.update(dt, game_scene)
            if not projectile.is_dead:
                alive_projectiles.append(projectile)
        self.projectiles = alive_projectiles

    def _draw_projectiles(self, screen, camera):
        for projectile in self.projectiles:
            projectile.draw(screen, camera)

    def draw(self, screen, camera):
        if self.is_dead:
            return
        self._draw_projectiles(screen, camera)
        super().draw(screen, camera)
