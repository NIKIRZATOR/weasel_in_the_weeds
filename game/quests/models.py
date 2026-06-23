from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QuestObjectiveDefinition:
    kind: str
    text_key: str
    flag: str | None = None
    item_id: str | None = None
    quantity: int = 1


@dataclass(frozen=True)
class QuestDefinition:
    id: str
    title_key: str
    description_key: str
    category: str = "main"
    sort_order: int = 0
    required_flags: tuple[str, ...] = field(default_factory=tuple)
    objectives: tuple[QuestObjectiveDefinition, ...] = field(default_factory=tuple)

