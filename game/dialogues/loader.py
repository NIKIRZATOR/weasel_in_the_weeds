import json
from pathlib import Path

from settings import DIALOGUES_DIR


def load_dialogue(dialogue_file):
    if not dialogue_file:
        return None

    path = Path(dialogue_file)
    if not path.is_absolute():
        path = DIALOGUES_DIR / path

    return json.loads(path.read_text(encoding="utf-8"))
