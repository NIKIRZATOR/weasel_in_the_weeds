from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from game.quests.models import QuestDefinition, QuestObjectiveDefinition
from settings import LEVELS_DIR


QUESTS_FILE_NAME = "quests.json"


def _optional_str(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _iter_level_quest_files():
    if not LEVELS_DIR.exists():
        return []
    return sorted(path for path in LEVELS_DIR.glob(f"*/{QUESTS_FILE_NAME}") if path.is_file())


@lru_cache(maxsize=1)
def get_quest_definitions() -> tuple[QuestDefinition, ...]:
    quest_definitions: list[QuestDefinition] = []
    for quest_file_path in _iter_level_quest_files():
        level_key = quest_file_path.parent.name
        raw_catalog = json.loads(quest_file_path.read_text(encoding="utf-8"))
        for quest_id, raw_quest in raw_catalog.items():
            if not isinstance(raw_quest, dict):
                continue

            objectives: list[QuestObjectiveDefinition] = []
            for index, raw_objective in enumerate(raw_quest.get("objectives", []), start=1):
                if not isinstance(raw_objective, dict):
                    continue
                objective_id = str(raw_objective.get("id") or f"{quest_id}_objective_{index}").strip()
                if not objective_id:
                    continue
                objectives.append(
                    QuestObjectiveDefinition(
                        id=objective_id,
                        kind=str(raw_objective.get("kind", "event")).strip() or "event",
                        text_key=str(raw_objective.get("text_key", "")).strip(),
                        target=_optional_str(raw_objective.get("target")),
                        required=max(1, int(raw_objective.get("required", raw_objective.get("quantity", 1)))),
                        legacy_flag=_optional_str(raw_objective.get("legacy_flag") or raw_objective.get("flag")),
                    )
                )

            quest_definitions.append(
                QuestDefinition(
                    id=str(quest_id).strip(),
                    level_key=level_key,
                    title_key=str(raw_quest.get("title_key", "")).strip(),
                    description_key=str(raw_quest.get("description_key", "")).strip(),
                    category=str(raw_quest.get("category", "main")).strip() or "main",
                    sort_order=int(raw_quest.get("sort_order", 0)),
                    required_flags=tuple(
                        str(flag).strip() for flag in raw_quest.get("required_flags", []) if str(flag).strip()
                    ),
                    objectives=tuple(objectives),
                    activation_dialogue_file=_optional_str(raw_quest.get("activation_dialogue_file")),
                )
            )
    return tuple(quest_definitions)
