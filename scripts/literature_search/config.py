from __future__ import annotations

import hashlib
import json
from dataclasses import MISSING, dataclass
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
    parser_contract_version: int = 1
    chunking_contract_version: int = 1
    embedding_contract_version: int = 1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchConfig":
        values: Dict[str, Any] = {}
        for field, definition in cls.__dataclass_fields__.items():
            if field in data:
                values[field] = data[field]
            elif definition.default is not MISSING:
                values[field] = definition.default
            else:
                raise KeyError(field)
        return cls(**values)

    def to_dict(self) -> Dict[str, Any]:
        return {
            field: getattr(self, field) for field in self.__dataclass_fields__
        }

    def resolve_index_path(
        self, repo_root: Path, override: Optional[str] = None
    ) -> Path:
        value = Path(override or self.index_path).expanduser()
        return value if value.is_absolute() else repo_root / value

    def embedding_contract_hash(self) -> str:
        contract = {
            "version": self.embedding_contract_version,
            "model_name": self.model_name,
            "model_revision": self.model_revision,
            "document_prefix": "passage: ",
            "query_prefix": "query: ",
            "tokenizer_revision": self.model_revision,
            "parser_contract_version": self.parser_contract_version,
            "chunking_contract_version": self.chunking_contract_version,
            "chunk_max_chars": self.chunk_max_chars,
            "chunk_overlap_chars": self.chunk_overlap_chars,
        }
        payload = json.dumps(
            contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_config(path: Optional[Path] = None) -> SearchConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return SearchConfig.from_dict(data)
