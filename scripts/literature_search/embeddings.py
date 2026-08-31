from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import numpy as np


class EmbeddingBackend:
    def __init__(
        self,
        model_name: str,
        revision: str,
        cache_folder: Optional[Path] = None,
        local_files_only: bool = False,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "向量后端不可用：当前解释器没有 sentence-transformers。\n"
                "唯一受支持的入口是仓库根目录下的 uv 项目环境：\n"
                "  uv run --project scripts/literature_search --locked "
                "python -m scripts.literature_search <子命令>\n"
                "不要使用 .cache/literature-search/venv（历史遗留，依赖不完整）、"
                "系统 python3 或 conda 环境——它们都缺向量后端。"
            ) from error
        self.model = SentenceTransformer(
            model_name,
            revision=revision,
            cache_folder=str(cache_folder) if cache_folder else None,
            local_files_only=local_files_only,
        )

    def _encode(self, texts: Sequence[str], prefix: str, batch_size: int) -> np.ndarray:
        values = [prefix + text for text in texts]
        vectors = self.model.encode(
            values,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=len(values) > batch_size,
        )
        return np.asarray(vectors, dtype=np.float32)

    def encode_documents(self, texts: Sequence[str], batch_size: int) -> np.ndarray:
        return self._encode(texts, "passage: ", batch_size)

    def encode_query(self, text: str) -> np.ndarray:
        return self._encode([text], "query: ", 1)[0]


def vector_scores(query_vector: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    if vectors.ndim != 2 or query_vector.ndim != 1:
        raise ValueError("向量维度无效")
    if vectors.shape[1] != query_vector.shape[0]:
        raise ValueError("查询向量与索引向量维度不一致")
    return vectors @ query_vector
