from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


CATALOG_PATH = Path(__file__).with_name("solid_object_catalog.json")
CATALOG: dict[str, dict] = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
SOLID_OBJECT_TEMPLATES: dict[str, dict] = CATALOG.get("objects", {})
SOLID_OBJECT_SETS: dict[str, list[dict]] = CATALOG.get("sets", {})


def get_solid_object_template(template_id: str) -> dict | None:
    template = SOLID_OBJECT_TEMPLATES.get(template_id)
    return deepcopy(template) if template is not None else None


def get_solid_object_set(set_id: str) -> list[dict]:
    return deepcopy(SOLID_OBJECT_SETS.get(set_id, []))
