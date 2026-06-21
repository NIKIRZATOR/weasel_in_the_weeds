from game.entities.enemies.base import Enemy
from game.entities.enemies.bosses import BaseBossEnemy, ForestGuardianBoss
from game.entities.enemies.projectiles import RangedProjectile
from game.entities.enemies.types.archer import ArcherEnemy
from game.entities.enemies.types.charger import ChargerEnemy
from game.entities.enemies.types.melee_grunt import MeleeGruntEnemy
from game.entities.enemies.types.shaman import ShamanEnemy
from game.entities.enemies.types.spearman import SpearmanEnemy

MeleeEnemy = MeleeGruntEnemy
RangedEnemy = ArcherEnemy

__all__ = [
    "ArcherEnemy",
    "BaseBossEnemy",
    "ChargerEnemy",
    "Enemy",
    "ForestGuardianBoss",
    "MeleeEnemy",
    "MeleeGruntEnemy",
    "RangedEnemy",
    "RangedProjectile",
    "ShamanEnemy",
    "SpearmanEnemy",
]
