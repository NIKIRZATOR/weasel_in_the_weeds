from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QuestObjectiveDefinition:
    id: str
    kind: str
    text_key: str
    target: str | None = None
    required: int = 1
    legacy_flag: str | None = None


@dataclass(frozen=True)
class QuestDefinition:
    id: str
    level_key: str
    title_key: str
    description_key: str
    category: str = "main"
    sort_order: int = 0
    required_flags: tuple[str, ...] = field(default_factory=tuple)
    objectives: tuple[QuestObjectiveDefinition, ...] = field(default_factory=tuple)
    activation_dialogue_file: str | None = None
