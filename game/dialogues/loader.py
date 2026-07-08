import json
from pathlib import Path

from settings import DIALOGUES_DIR


def load_dialogue(dialogue_file, base_dir=None):
    if not dialogue_file:
        return None

    path = Path(dialogue_file)
    if not path.is_absolute():
        if base_dir is not None:
            candidate = Path(base_dir) / path
            if candidate.exists():
                path = candidate
            else:
                path = DIALOGUES_DIR / path
        else:
            path = DIALOGUES_DIR / path

    return json.loads(path.read_text(encoding="utf-8"))
