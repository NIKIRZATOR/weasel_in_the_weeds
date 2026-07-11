from __future__ import annotations

import json
from pathlib import Path

from game.dialogues import load_dialogue


class TriggerManager:
    def __init__(self, game_scene):
        self.game_scene = game_scene
        self.triggers = self._load_triggers()
        self.pending_events: list[tuple[str, dict]] = []

    def queue_event(self, event_name, **payload):
        self.pending_events.append((str(event_name), dict(payload)))

    def process_pending_events(self):
        while self.pending_events:
            event_name, payload = self.pending_events.pop(0)
            if self.emit(event_name, **payload):
                return True
        return False

    def emit(self, event_name, **payload):
        triggered_any = False
        for trigger in self.triggers:
            if not self._matches_event(trigger, event_name):
                continue
            if not self._conditions_met(trigger, payload):
                continue
            self._execute_trigger(trigger, payload)
            triggered_any = True
            if self.game_scene.app.scene is not self.game_scene:
                return True
        return triggered_any

    def _load_triggers(self):
        triggers_path = self._resolve_triggers_path()
        if triggers_path is None or not triggers_path.exists():
            return []

        raw_data = json.loads(triggers_path.read_text(encoding="utf-8"))
        raw_triggers = raw_data.get("triggers", [])
        if not isinstance(raw_triggers, list):
            return []

        normalized = []
        for index, raw_trigger in enumerate(raw_triggers):
            if not isinstance(raw_trigger, dict):
                continue
            trigger_id = str(
                raw_trigger.get("id")
                or f"{self.game_scene.level_key}:{raw_trigger.get('event', 'trigger')}:{index}"
            )
            normalized.append(
                {
                    "id": trigger_id,
                    "event": str(raw_trigger.get("event", "")).strip(),
                    "conditions": raw_trigger.get("conditions", {}) if isinstance(raw_trigger.get("conditions", {}), dict) else {},
                    "actions": raw_trigger.get("actions", []) if isinstance(raw_trigger.get("actions", []), list) else [],
                }
            )
        return normalized

    def _resolve_triggers_path(self):
        level_path = Path(self.game_scene.level_path)
        if level_path.is_dir():
            return level_path / "triggers.json"
        return level_path.parent / "triggers.json"

    def _matches_event(self, trigger, event_name):
        return trigger.get("event") == str(event_name)

    def _conditions_met(self, trigger, payload):
        conditions = trigger.get("conditions", {})
        trigger_id = trigger.get("id", "")
        if conditions.get("once", False) and self.game_scene.has_trigger_fired(trigger_id):
            return False

        required_flags = conditions.get("required_flags", [])
        if required_flags and not self.game_scene.player.has_flags(required_flags):
            return False

        blocked_flags = conditions.get("blocked_flags", [])
        if blocked_flags and any(self.game_scene.player.has_flag(flag) for flag in blocked_flags):
            return False

        match_payload = conditions.get("match", {})
        if isinstance(match_payload, dict):
            for key, expected_value in match_payload.items():
                if payload.get(key) != expected_value:
                    return False
        return True

    def _execute_trigger(self, trigger, payload):
        trigger_id = trigger.get("id", "")
        flagged_world_refresh_needed = False

        for action in trigger.get("actions", []):
            if not isinstance(action, dict):
                continue
            action_type = str(action.get("type", "")).strip().lower()
            if action_type == "dialogue":
                self._run_dialogue_action(action)
                continue
            if action_type == "music":
                music_key = action.get("music_key")
                if music_key:
                    self.game_scene.app.audio.play_music(str(music_key))
                continue
            if action_type == "sound":
                sound_key = action.get("sound_key")
                if sound_key:
                    self.game_scene.app.audio.play_sound(str(sound_key), volume=float(action.get("volume", 1.0)))
                continue
            if action_type == "set_flag":
                if self.game_scene.player.set_flag(action.get("flag")):
                    flagged_world_refresh_needed = True
                continue
            if action_type == "unset_flag":
                if self.game_scene.player.unset_flag(action.get("flag")):
                    flagged_world_refresh_needed = True
                continue
            if action_type == "message":
                text = str(action.get("text", "")).strip()
                if text:
                    self.game_scene.last_interaction_message = text
                    self.game_scene.last_interaction_timer = max(
                        0.1,
                        float(action.get("duration", 2.0)),
                    )

        if trigger.get("conditions", {}).get("once", False):
            self.game_scene.mark_trigger_fired(trigger_id)
        if flagged_world_refresh_needed:
            self.game_scene.refresh_flag_controlled_world_objects()

    def _run_dialogue_action(self, action):
        dialogue_file = action.get("dialogue_file")
        if not dialogue_file:
            return
        try:
            dialogue = load_dialogue(
                dialogue_file,
                base_dir=self._resolve_triggers_path().parent if self._resolve_triggers_path() is not None else None,
            )
        except (OSError, ValueError) as error:
            print(f"Trigger dialogue load failed for {dialogue_file}: {error}")
            return

        from game.scenes.dialogue_scene import DialogueScene

        speaker_name = action.get("speaker_name")
        self.game_scene.app.set_scene(
            DialogueScene(
                self.game_scene.app,
                self.game_scene,
                dialogue=dialogue,
                speaker_name=str(speaker_name) if speaker_name else None,
            )
        )
