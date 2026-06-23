from __future__ import annotations

from game.quests.catalog import get_quest_definitions


class QuestManager:
    def __init__(self, player):
        self.player = player
        self.quest_definitions = tuple(sorted(get_quest_definitions(), key=lambda quest: quest.sort_order))

    def get_active_main_quest(self):
        for quest in self.quest_definitions:
            if quest.category != "main":
                continue
            if self.get_quest_status(quest) == "active":
                return quest
        return None

    def get_next_main_quest(self):
        found_active = False
        for quest in self.quest_definitions:
            if quest.category != "main":
                continue
            status = self.get_quest_status(quest)
            if status == "active":
                found_active = True
                continue
            if found_active and status != "completed":
                return quest
        if found_active:
            return None
        for quest in self.quest_definitions:
            if quest.category != "main":
                continue
            if self.get_quest_status(quest) != "completed":
                return quest
        return None

    def get_active_and_next_main_quests(self):
        result = []
        active = self.get_active_main_quest()
        if active is not None:
            result.append((active, "active"))
        next_quest = self.get_next_main_quest()
        if next_quest is not None and next_quest is not active:
            result.append((next_quest, "next"))
        return result

    def get_quest_log_entries(self, category="main"):
        entries = []
        next_quest = self.get_next_main_quest()
        for quest in self.quest_definitions:
            if category is not None and quest.category != category:
                continue
            status = self.get_quest_status(quest)
            if status == "completed":
                entries.append((quest, "completed"))
            elif status == "active":
                entries.append((quest, "active"))
            elif next_quest is quest:
                entries.append((quest, "next"))
        return entries

    def get_visible_quests(self, category=None):
        visible = []
        for quest in self.quest_definitions:
            if category is not None and quest.category != category:
                continue
            status = self.get_quest_status(quest)
            if status == "inactive":
                continue
            visible.append((quest, status))
        return visible

    def get_quest_status(self, quest):
        if self.is_quest_completed(quest):
            return "completed"
        if self._requirements_met(quest):
            return "active"
        return "inactive"

    def is_quest_completed(self, quest):
        return all(self.is_objective_completed(objective) for objective in quest.objectives)

    def is_objective_completed(self, objective):
        if objective.kind == "flag":
            return bool(objective.flag) and self.player.has_flag(objective.flag)
        if objective.kind == "item":
            return bool(objective.item_id) and self.player.has_item(objective.item_id, objective.quantity)
        return False

    def build_objective_status(self, objective, localizer):
        text = localizer.t(objective.text_key)
        if objective.kind == "item":
            current = self.player.inventory.count_item(objective.item_id) + self.player.quest_inventory.count_item(
                objective.item_id
            )
            text = localizer.t(objective.text_key, current=current, required=objective.quantity)
        return {
            "text": text,
            "completed": self.is_objective_completed(objective),
        }

    def _requirements_met(self, quest):
        return self.player.has_flags(quest.required_flags)
