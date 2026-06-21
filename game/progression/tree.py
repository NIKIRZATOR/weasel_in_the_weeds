from __future__ import annotations

from game.items.models import CharacterStats
from game.progression.models import ProgressionBonuses, SkillNodeDefinition


SKILL_TREE_NODES: dict[str, SkillNodeDefinition] = {
    "vitality_1": SkillNodeDefinition(
        id="vitality_1",
        position=(180, 120),
        icon_path="assets/ui/progression_nodes/vitality_1.png",
        bonuses=ProgressionBonuses(stats=CharacterStats(max_health=10)),
    ),
    "vitality_2": SkillNodeDefinition(
        id="vitality_2",
        position=(120, 200),
        requires=("vitality_1",),
        icon_path="assets/ui/progression_nodes/vitality_2.png",
        bonuses=ProgressionBonuses(stats=CharacterStats(max_health=12)),
    ),
    "iron_skin": SkillNodeDefinition(
        id="iron_skin",
        position=(235, 230),
        requires=("vitality_1",),
        icon_path="assets/ui/progression_nodes/iron_skin.png",
        bonuses=ProgressionBonuses(stats=CharacterStats(defense=1)),
    ),
    "endurance_1": SkillNodeDefinition(
        id="endurance_1",
        position=(540, 120),
        icon_path="assets/ui/progression_nodes/endurance_1.png",
        bonuses=ProgressionBonuses(stats=CharacterStats(max_stamina=8)),
    ),
    "endurance_2": SkillNodeDefinition(
        id="endurance_2",
        position=(600, 200),
        requires=("endurance_1",),
        icon_path="assets/ui/progression_nodes/endurance_2.png",
        bonuses=ProgressionBonuses(stats=CharacterStats(max_stamina=10)),
    ),
    "bow_focus": SkillNodeDefinition(
        id="bow_focus",
        position=(485, 230),
        requires=("endurance_1",),
        icon_path="assets/ui/progression_nodes/bow_focus.png",
        bonuses=ProgressionBonuses(bow_damage_bonus=2),
    ),
    "edge_1": SkillNodeDefinition(
        id="edge_1",
        position=(360, 88),
        icon_path="assets/ui/progression_nodes/edge_1.png",
        bonuses=ProgressionBonuses(stats=CharacterStats(attack=1)),
    ),
    "edge_2": SkillNodeDefinition(
        id="edge_2",
        position=(360, 176),
        requires=("edge_1",),
        icon_path="assets/ui/progression_nodes/edge_2.png",
        bonuses=ProgressionBonuses(stats=CharacterStats(attack=1)),
    ),
    "light_hands": SkillNodeDefinition(
        id="light_hands",
        position=(310, 264),
        requires=("edge_2",),
        icon_path="assets/ui/progression_nodes/light_hands.png",
        bonuses=ProgressionBonuses(light_stamina_cost_multiplier=0.85),
    ),
    "heavy_form": SkillNodeDefinition(
        id="heavy_form",
        position=(410, 264),
        requires=("edge_2",),
        icon_path="assets/ui/progression_nodes/heavy_form.png",
        bonuses=ProgressionBonuses(
            heavy_stamina_cost_multiplier=0.85,
            recovery_multiplier=0.9,
        ),
    ),
    "footwork": SkillNodeDefinition(
        id="footwork",
        position=(180, 352),
        icon_path="assets/ui/progression_nodes/footwork.png",
        bonuses=ProgressionBonuses(stats=CharacterStats(speed=10)),
    ),
    "battle_flow": SkillNodeDefinition(
        id="battle_flow",
        position=(250, 430),
        requires=("footwork",),
        icon_path="assets/ui/progression_nodes/battle_flow.png",
        bonuses=ProgressionBonuses(attack_move_speed_multiplier_bonus=0.2),
    ),
    "hunter_draw": SkillNodeDefinition(
        id="hunter_draw",
        position=(540, 352),
        requires=("bow_focus",),
        icon_path="assets/ui/progression_nodes/hunter_draw.png",
        bonuses=ProgressionBonuses(
            charged_stamina_cost_multiplier=0.9,
            charge_time_multiplier=0.8,
        ),
    ),
    "relentless": SkillNodeDefinition(
        id="relentless",
        position=(360, 430),
        requires=("heavy_form",),
        icon_path="assets/ui/progression_nodes/relentless.png",
        bonuses=ProgressionBonuses(
            charged_damage_bonus=2,
            recovery_multiplier=0.9,
        ),
    ),
    "relentless_2": SkillNodeDefinition(
        id="relentless_2",
        position=(420, 490),
        requires=("relentless",),
        icon_path="assets/ui/progression_nodes/relentless_2.png",
        bonuses=ProgressionBonuses(
            charged_damage_bonus=4,
            recovery_multiplier=0.85,
        ),
    ),
}


def get_skill_node_definition(node_id: str) -> SkillNodeDefinition | None:
    return SKILL_TREE_NODES.get(str(node_id))


def build_progression_bonuses(unlocked_node_ids: set[str]) -> ProgressionBonuses:
    total = ProgressionBonuses()
    for node_id in unlocked_node_ids:
        node = get_skill_node_definition(node_id)
        if node is None:
            continue
        total = total + node.bonuses
    return total
