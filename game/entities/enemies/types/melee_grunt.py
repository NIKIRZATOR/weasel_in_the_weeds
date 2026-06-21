from __future__ import annotations

from game.core.vector import Vector2
from game.entities.enemies.ai.states import CHASE
from game.entities.enemies.ai.steering import entity_distance
from game.entities.enemies.base import Enemy


class MeleeGruntEnemy(Enemy):
    BODY_HITBOX = {
        "width": 21,
        "height": 21,
        "offset_x": 5,
        "offset_y": 11,
    }
    HURTBOX = {
        "width": 19,
        "height": 20,
        "offset_x": 6,
        "offset_y": 10,
    }
    ATTACK_HITBOX = {
        "width": 20,
        "height": 18,
        "offset_x": 18,
        "offset_y": 12,
        "mirror_with_facing": True,
    }
    COLLISION_CIRCLE = {
        "radius": 10.5,
    }
    LOOT_TABLE = (
        {"item_id": "bone", "min_quantity": 1, "max_quantity": 1, "chance": 0.45},
        {"item_id": "stick", "min_quantity": 1, "max_quantity": 2, "chance": 0.35},
        {"coins": 2, "chance": 0.5},
    )

    def __init__(
        self,
        x,
        y,
        width,
        height,
        name="melee_enemy",
        max_health=20,
        speed=75,
        damage=6,
        melee_range=50,
        detection_radius=150,
        attack_cooldown=1.0,
        patrol_radius=140,
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
            color=(220, 55, 55),
            xp_reward=xp_reward,
            **hitbox_kwargs,
        )
        self.melee_range = float(melee_range)
        self.attack_radius = self.melee_range

    def update(self, dt, game_scene):
        super().update(dt, game_scene)
        if self.is_dead or self.behavior_state != CHASE:
            return
        player = game_scene.player
        player_center = player.get_center()
        distance = entity_distance(self, player)
        if distance <= self.melee_range:
            if not self.attack_cooldown.is_active():
                self.activate_attack_hitbox(0.08)
                player.take_damage(self.damage)
                self.attack_cooldown.start()
            return
        previous_position = Vector2(self.position.x, self.position.y)
        self._move_towards(player_center.x, player_center.y, dt, game_scene, use_pathfinding=True)
        self._update_stuck_state(dt, previous_position, game_scene)
