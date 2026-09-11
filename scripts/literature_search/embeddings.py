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
        device: str = "auto",
    ) -> None:
        try:
            import torch
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "向量后端未安装。请按 README 使用 uv sync 同步独立项目环境。"
            ) from error
        if device not in {"auto", "cpu", "mps"}:
            raise ValueError(f"未知向量设备：{device}")
        mps_available = bool(torch.backends.mps.is_available())
        if device == "mps" and not mps_available:
            raise RuntimeError("已指定 MPS，但当前原生 PyTorch 或主机不支持 MPS")
        selected_device = "mps" if device == "auto" and mps_available else device
        if selected_device == "auto":
            selected_device = "cpu"
        self.requested_device = device
        self.fallback_reason: Optional[str] = None
        parameters = {
            "revision": revision,
            "cache_folder": str(cache_folder) if cache_folder else None,
            "local_files_only": local_files_only,
        }
        try:
            self.model = SentenceTransformer(
                model_name,
                device=selected_device,
                **parameters,
            )
        except RuntimeError as error:
            if device != "auto" or selected_device != "mps":
                raise
            self.fallback_reason = f"MPS 加载失败，已回退 CPU：{error}"
            self.model = SentenceTransformer(model_name, device="cpu", **parameters)

    @property
    def device(self) -> str:
        return str(self.model.device)

    def _encode(self, texts: Sequence[str], prefix: str, batch_size: int) -> np.ndarray:
        values = [prefix + text for text in texts]
        parameters = {
            "batch_size": batch_size,
            "normalize_embeddings": True,
            "convert_to_numpy": True,
            "show_progress_bar": len(values) > batch_size,
        }
        try:
            vectors = self.model.encode(values, **parameters)
        except RuntimeError as error:
            if self.requested_device != "auto" or self.device != "mps":
                raise
            self.fallback_reason = f"MPS 编码失败，已回退 CPU：{error}"
            self.model.cpu()
            vectors = self.model.encode(values, **parameters)
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
