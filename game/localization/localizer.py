from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Localizer:
    def __init__(self, translations_dir: str | Path | None = None, language: str = "ru"):
        self.translations_dir = Path(translations_dir or Path(__file__).with_name("translations"))
        self.language = language
        self._cache: dict[str, dict[str, Any]] = {}
        self._fallback_language = "en"

    def set_language(self, language: str):
        self.language = language

    def get_language(self) -> str:
        return self.language

    def available_languages(self) -> list[str]:
        languages = []
        if self.translations_dir.exists():
            for path in self.translations_dir.glob("*.json"):
                languages.append(path.stem)
        return sorted(languages)

    def t(self, key: str, **kwargs: Any) -> str:
        value = self._lookup(self.language, key)
        if value is None:
            value = self._lookup(self._fallback_language, key)
        if value is None:
            return key
        if kwargs:
            try:
                return str(value).format(**kwargs)
            except Exception:
                return str(value)
        return str(value)

    def _lookup(self, language: str, key: str):
        data = self._load_language(language)
        current: Any = data
        for part in key.split('.'):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def _load_language(self, language: str) -> dict[str, Any]:
        if language in self._cache:
            return self._cache[language]

        path = self.translations_dir / f"{language}.json"
        if not path.exists():
            self._cache[language] = {}
            return self._cache[language]

        self._cache[language] = json.loads(path.read_text(encoding="utf-8"))
        return self._cache[language]


_default_localizer: Localizer | None = None


def get_localizer() -> Localizer:
    global _default_localizer
    if _default_localizer is None:
        _default_localizer = Localizer()
    return _default_localizer
