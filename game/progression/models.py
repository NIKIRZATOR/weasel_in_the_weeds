from __future__ import annotations

from dataclasses import dataclass, field

from game.items.models import CharacterStats
from game.localization import get_localizer


@dataclass(frozen=True)
class ProgressionBonuses:
    stats: CharacterStats = field(default_factory=CharacterStats)
    attack_move_speed_multiplier_bonus: float = 0.0
    light_stamina_cost_multiplier: float = 1.0
    heavy_stamina_cost_multiplier: float = 1.0
    charged_stamina_cost_multiplier: float = 1.0
    bow_damage_bonus: int = 0
    charged_damage_bonus: int = 0
    recovery_multiplier: float = 1.0
    charge_time_multiplier: float = 1.0

    def __add__(self, other: "ProgressionBonuses") -> "ProgressionBonuses":
        return ProgressionBonuses(
            stats=self.stats + other.stats,
            attack_move_speed_multiplier_bonus=(
                self.attack_move_speed_multiplier_bonus + other.attack_move_speed_multiplier_bonus
            ),
            light_stamina_cost_multiplier=self.light_stamina_cost_multiplier * other.light_stamina_cost_multiplier,
            heavy_stamina_cost_multiplier=self.heavy_stamina_cost_multiplier * other.heavy_stamina_cost_multiplier,
            charged_stamina_cost_multiplier=(
                self.charged_stamina_cost_multiplier * other.charged_stamina_cost_multiplier
            ),
            bow_damage_bonus=self.bow_damage_bonus + other.bow_damage_bonus,
            charged_damage_bonus=self.charged_damage_bonus + other.charged_damage_bonus,
            recovery_multiplier=self.recovery_multiplier * other.recovery_multiplier,
            charge_time_multiplier=self.charge_time_multiplier * other.charge_time_multiplier,
        )


@dataclass(frozen=True)
class SkillNodeDefinition:
    id: str
    position: tuple[int, int]
    requires: tuple[str, ...] = ()
    icon_path: str | None = None
    bonuses: ProgressionBonuses = field(default_factory=ProgressionBonuses)

    def localized_name(self) -> str:
        localizer = get_localizer()
        key = f"ui.progression.nodes.{self.id}.name"
        translated = localizer.t(key)
        return translated if translated != key else self.id.replace("_", " ").title()

    def localized_description(self) -> str:
        localizer = get_localizer()
        key = f"ui.progression.nodes.{self.id}.description"
        translated = localizer.t(key)
        return translated if translated != key else self.localized_name()
