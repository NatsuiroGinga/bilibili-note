from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]
DEFAULT_CONFIG_PATH = PACKAGE_DIR / "config.json"


@dataclass(frozen=True)
class SearchConfig:
    schema_version: int
    input_glob: str
    index_path: str
    model_name: str
    model_revision: str
    batch_size: int
    chunk_max_chars: int
    chunk_overlap_chars: int
    rrf_constant: int
    default_top_k: int
    online_limit: int
    online_timeout_seconds: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchConfig":
        return cls(**{field: data[field] for field in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        return {
            field: getattr(self, field) for field in self.__dataclass_fields__
        }

    def resolve_index_path(
        self, repo_root: Path, override: Optional[str] = None
    ) -> Path:
        value = Path(override or self.index_path).expanduser()
        return value if value.is_absolute() else repo_root / value


def load_config(path: Optional[Path] = None) -> SearchConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return SearchConfig.from_dict(data)
