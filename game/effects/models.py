from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EffectType(str, Enum):
    HEALTH_REGENERATION = "health_regeneration"
    STAMINA_REGENERATION = "stamina_regeneration"
    ARMOR_INCREASED = "armor_increased"
    DAMAGE_INCREASED = "damage_increased"
    SLOWED = "slowed"
    DAMAGE_REDUCED = "damage_reduced"
    FATIGUE = "fatigue"


@dataclass(frozen=True)
class EffectDefinition:
    id: EffectType
    is_positive: bool
    description: str


EFFECT_DEFINITIONS: dict[EffectType, EffectDefinition] = {
    EffectType.HEALTH_REGENERATION: EffectDefinition(
        EffectType.HEALTH_REGENERATION, True, "Restores health every second."
    ),
    EffectType.STAMINA_REGENERATION: EffectDefinition(
        EffectType.STAMINA_REGENERATION, True, "Restores stamina every second."
    ),
    EffectType.ARMOR_INCREASED: EffectDefinition(
        EffectType.ARMOR_INCREASED, True, "Increases armor."
    ),
    EffectType.DAMAGE_INCREASED: EffectDefinition(
        EffectType.DAMAGE_INCREASED, True, "Increases outgoing damage."
    ),
    EffectType.SLOWED: EffectDefinition(
        EffectType.SLOWED, False, "Reduces movement speed."
    ),
    EffectType.DAMAGE_REDUCED: EffectDefinition(
        EffectType.DAMAGE_REDUCED, False, "Reduces outgoing damage."
    ),
    EffectType.FATIGUE: EffectDefinition(
        EffectType.FATIGUE, False, "Increases stamina costs."
    ),
}


def get_effect_definition(effect_type: EffectType | str) -> EffectDefinition | None:
    try:
        normalized = effect_type if isinstance(effect_type, EffectType) else EffectType(effect_type)
    except ValueError:
        return None
    return EFFECT_DEFINITIONS.get(normalized)


@dataclass
class ActiveEffect:
    effect_type: EffectType
    value: float
    duration: float
    remaining: float
    source_item_id: str | None = None

    @classmethod
    def create(
        cls,
        effect_type: EffectType | str,
        value: float,
        duration: float,
        source_item_id: str | None = None,
    ) -> "ActiveEffect":
        normalized = effect_type if isinstance(effect_type, EffectType) else EffectType(effect_type)
        normalized_duration = max(0.0, float(duration))
        return cls(normalized, float(value), normalized_duration, normalized_duration, source_item_id)

    def refresh_from(self, other: "ActiveEffect") -> None:
        """Replace the effect parameters and restart it without stacking its strength."""
        self.value = other.value
        self.duration = other.duration
        self.remaining = other.duration
        self.source_item_id = other.source_item_id
