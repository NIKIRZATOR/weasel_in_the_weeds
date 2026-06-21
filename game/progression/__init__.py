from game.progression.models import ProgressionBonuses, SkillNodeDefinition
from game.progression.tree import SKILL_TREE_NODES, build_progression_bonuses, get_skill_node_definition


def get_xp_to_next_level(level: int) -> int:
    level = max(1, int(level))
    return 20 + (level - 1) * 15


__all__ = [
    "ProgressionBonuses",
    "SkillNodeDefinition",
    "SKILL_TREE_NODES",
    "build_progression_bonuses",
    "get_skill_node_definition",
    "get_xp_to_next_level",
]
