from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


CATALOG_PATH = Path(__file__).with_name("gatherable_catalog.json")
GATHERABLE_TEMPLATES: dict[str, dict] = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def get_gatherable_template(template_id: str) -> dict | None:
    template = GATHERABLE_TEMPLATES.get(template_id)
    return deepcopy(template) if template is not None else None
