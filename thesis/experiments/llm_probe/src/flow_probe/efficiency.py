"""训练与推理效率的本地可复现计时。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any


def _cuda_peak_memory_bytes() -> int | None:
    try:
        import torch
    except ImportError:
        return None
    if not torch.cuda.is_available():
        return None
    return int(torch.cuda.max_memory_allocated())


def _reset_cuda_peak_memory() -> None:
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


@dataclass
class RunTimer:
    """记录一次训练或推理运行的墙钟时间、令牌与显存。"""

    sample_count: int
    input_tokens: int = 0
    generated_tokens: int = 0
    _started_at: float | None = field(default=None, init=False, repr=False)
    _ended_at: float | None = field(default=None, init=False, repr=False)

    def __enter__(self) -> RunTimer:
        if self.sample_count <= 0:
            raise ValueError("sample_count 必须大于 0")
        _reset_cuda_peak_memory()
        self._started_at = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._ended_at = time.perf_counter()

    def record_tokens(self, input_tokens: int, generated_tokens: int) -> None:
        """累加实际分词器统计，不用字符数估算。"""
        if input_tokens < 0 or generated_tokens < 0:
            raise ValueError("令牌数不能为负数")
        self.input_tokens += input_tokens
        self.generated_tokens += generated_tokens

    def summary(self) -> dict[str, Any]:
        """返回可写入 JSON 的效率摘要。"""
        if self._started_at is None or self._ended_at is None:
            raise RuntimeError("计时器尚未完成")
        wall_seconds = max(self._ended_at - self._started_at, 1e-12)
        return {
            "sample_count": self.sample_count,
            "input_tokens": self.input_tokens,
            "generated_tokens": self.generated_tokens,
            "wall_seconds": wall_seconds,
            "samples_per_second": self.sample_count / wall_seconds,
            "tokens_per_second": (self.input_tokens + self.generated_tokens) / wall_seconds,
            "peak_gpu_memory_bytes": _cuda_peak_memory_bytes(),
        }
