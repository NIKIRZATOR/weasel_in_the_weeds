from __future__ import annotations

from game.quests.models import QuestDefinition, QuestObjectiveDefinition


QUEST_DEFINITIONS: tuple[QuestDefinition, ...] = (
    QuestDefinition(
        id="meet_hermit",
        title_key="ui.quests.main.meet_hermit.title",
        description_key="ui.quests.main.meet_hermit.description",
        sort_order=10,
        objectives=(
            QuestObjectiveDefinition(
                kind="flag",
                text_key="ui.quests.main.meet_hermit.objective",
                flag="met_mouse_hermit",
            ),
        ),
    ),
    QuestDefinition(
        id="enter_forest_edge",
        title_key="ui.quests.main.enter_forest_edge.title",
        description_key="ui.quests.main.enter_forest_edge.description",
        sort_order=20,
        required_flags=("met_mouse_hermit",),
        objectives=(
            QuestObjectiveDefinition(
                kind="flag",
                text_key="ui.quests.main.enter_forest_edge.objective",
                flag="entered_forest_edge",
            ),
        ),
    ),
    QuestDefinition(
        id="enter_deep_forest",
        title_key="ui.quests.main.enter_deep_forest.title",
        description_key="ui.quests.main.enter_deep_forest.description",
        sort_order=30,
        required_flags=("entered_forest_edge",),
        objectives=(
            QuestObjectiveDefinition(
                kind="flag",
                text_key="ui.quests.main.enter_deep_forest.objective",
                flag="entered_dart_forest",
            ),
        ),
    ),
    QuestDefinition(
        id="defeat_guardian",
        title_key="ui.quests.main.defeat_guardian.title",
        description_key="ui.quests.main.defeat_guardian.description",
        sort_order=40,
        required_flags=("entered_dart_forest",),
        objectives=(
            QuestObjectiveDefinition(
                kind="flag",
                text_key="ui.quests.main.defeat_guardian.objective",
                flag="boss_defeated",
            ),
        ),
    ),
)


def get_quest_definitions() -> tuple[QuestDefinition, ...]:
    return QUEST_DEFINITIONS

