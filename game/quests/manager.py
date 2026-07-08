from __future__ import annotations

from game.quests.catalog import get_quest_definitions


class QuestManager:
    def __init__(self, player):
        self.player = player
        self.quest_definitions = tuple(
            sorted(get_quest_definitions(), key=lambda quest: (quest.level_key, quest.sort_order, quest.id))
        )
        self.quest_definitions_by_id = {quest.id: quest for quest in self.quest_definitions}
        self.player.quest_event_callback = self.record_event
        self.on_quest_activated = None
        self._sync_all_progress(notify=False)

    def record_event(self, event_id, amount=1):
        event_key = str(event_id).strip()
        amount = max(0, int(amount))
        if not event_key or amount <= 0:
            return False

        updated = False
        previous_statuses = self._snapshot_statuses()
        for quest in self.quest_definitions:
            quest_state = self._get_or_create_quest_state(quest.id)
            for objective in quest.objectives:
                if objective.kind != "event" or objective.target != event_key:
                    continue
                objective_state = self._get_or_create_objective_state(quest_state, objective.id)
                previous = max(0, int(objective_state.get("current", 0)))
                current = min(objective.required, previous + amount)
                if current == previous:
                    continue
                objective_state["current"] = current
                objective_state["required"] = objective.required
                objective_state["completed"] = current >= objective.required
                updated = True

        if updated:
            self._sync_all_progress(previous_statuses=previous_statuses, notify=True)
        return updated

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
        quest_state = self._sync_quest_state(quest)
        if quest_state.get("completed", False):
            return "completed"
        if quest_state.get("started", False) or self._requirements_met(quest):
            return "active"
        return "inactive"

    def is_quest_completed(self, quest):
        return self._sync_quest_state(quest).get("completed", False)

    def is_objective_completed(self, quest, objective):
        completed, _current, _required = self._get_objective_progress(quest, objective)
        return completed

    def build_objective_status(self, quest, objective, localizer):
        completed, current, required = self._get_objective_progress(quest, objective)
        text = localizer.t(objective.text_key)
        if objective.kind in {"item", "event"}:
            text = localizer.t(objective.text_key, current=current, required=required)
        return {
            "text": text,
            "completed": completed,
        }

    def _snapshot_statuses(self):
        return {quest.id: self._compute_quest_status(quest) for quest in self.quest_definitions}

    def _compute_quest_status(self, quest):
        quest_state = self._get_or_create_quest_state(quest.id)
        if quest_state.get("completed", False):
            return "completed"
        if quest_state.get("started", False) or self._requirements_met(quest):
            return "active"
        return "inactive"

    def _sync_all_progress(self, previous_statuses=None, notify=False):
        previous_statuses = previous_statuses or {}
        activated_quests = []
        for quest in self.quest_definitions:
            previous_status = previous_statuses.get(quest.id)
            quest_state = self._sync_quest_state(quest)
            current_status = self._compute_quest_status(quest)
            if notify and previous_status != "active" and current_status == "active":
                if not quest_state.get("activation_shown", False):
                    quest_state["activation_shown"] = True
                    activated_quests.append(quest)
        for quest in activated_quests:
            if callable(self.on_quest_activated):
                self.on_quest_activated(quest)

    def _sync_quest_state(self, quest):
        quest_state = self._get_or_create_quest_state(quest.id)
        completed = bool(quest.objectives)
        has_progress = False
        for objective in quest.objectives:
            objective_completed, current, _required = self._sync_objective_state(quest_state, objective)
            completed = completed and objective_completed
            has_progress = has_progress or current > 0
        quest_state["started"] = bool(quest_state.get("started", False) or has_progress or self._requirements_met(quest))
        quest_state["completed"] = completed
        return quest_state

    def _sync_objective_state(self, quest_state, objective):
        completed, current, required = self._get_objective_progress_from_state(quest_state, objective)
        objective_state = self._get_or_create_objective_state(quest_state, objective.id)
        objective_state["current"] = current
        objective_state["required"] = required
        objective_state["completed"] = completed
        return completed, current, required

    def _get_objective_progress(self, quest, objective):
        quest_state = self._sync_quest_state(quest)
        return self._get_objective_progress_from_state(quest_state, objective)

    def _get_objective_progress_from_state(self, quest_state, objective):
        required = max(1, int(objective.required))
        current = 0
        if objective.kind == "flag":
            current = required if objective.target and self.player.has_flag(objective.target) else 0
        elif objective.kind == "item":
            current = self.player.inventory.count_item(objective.target) + self.player.quest_inventory.count_item(
                objective.target
            )
        elif objective.kind == "event":
            objective_state = self._get_or_create_objective_state(quest_state, objective.id)
            current = max(0, int(objective_state.get("current", 0)))
            legacy_flag = self._legacy_flag_for_objective(objective)
            if legacy_flag and self.player.has_flag(legacy_flag):
                current = max(current, required)
        current = min(current, required)
        return current >= required, current, required

    def _legacy_flag_for_objective(self, objective):
        if objective.legacy_flag:
            return objective.legacy_flag
        if objective.kind == "event" and objective.target and objective.target.startswith("flag:"):
            return objective.target[5:]
        return None

    def _get_or_create_quest_state(self, quest_id):
        state = self.player.quest_progress.setdefault(str(quest_id), {})
        state.setdefault("started", False)
        state.setdefault("completed", False)
        state.setdefault("activation_shown", False)
        state.setdefault("objectives", {})
        return state

    def _get_or_create_objective_state(self, quest_state, objective_id):
        objectives = quest_state.setdefault("objectives", {})
        state = objectives.setdefault(str(objective_id), {})
        state.setdefault("current", 0)
        state.setdefault("required", 1)
        state.setdefault("completed", False)
        return state

    def _requirements_met(self, quest):
        if not self.player.has_flags(quest.required_flags):
            return False
        return self._previous_main_quests_completed(quest)

    def _previous_main_quests_completed(self, quest):
        if quest.category != "main":
            return True

        for current in self.quest_definitions:
            if current is quest:
                break
            if current.category != quest.category:
                continue
            if not self.is_quest_completed(current):
                return False
        return True
