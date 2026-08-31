#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FT C00 selected-by-entity 的独立 LSPR24 零训练描述性评价入口。"""

from __future__ import annotations

import sys
from pathlib import Path

import ch3_ft_c01_c10_lspr24_descriptive_eval as core

core.RUN_ID = "ch3-ft-c00-lspr24-descriptive-eval-v1"
core.SCHEMA_VERSION = "ch3-ft-c00-lspr24-descriptive-eval-v1"
core.CELLS = ("c00",)
core.ENTRYPOINT_PATH = Path(__file__).resolve()
core.__doc__ = __doc__


if __name__ == "__main__":
    sys.exit(core.main())
