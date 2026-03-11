import json
from pathlib import Path
from typing import Any, Dict, List


class StaticJsonProvider:
    def __init__(self, path: str = "data/eu_specs.json") -> None:
        self.path = Path(path)
        self._cache: List[Dict[str, Any]] | None = None

    def get_cars(self, prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
        if self._cache is None:
            self._cache = json.loads(self.path.read_text(encoding="utf-8"))
        return self._cache