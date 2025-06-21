# storybook/meta.py - Story メタモデル
"""StoryMeta を定義するモジュール。"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, List, Type

from pydantic import BaseModel, Field


class StoryMeta(BaseModel):
    """Story のメタ情報"""

    id: str
    path: List[str]  # ["Button", "Primary"]
    title: str  # "Primary"
    factory: Callable[..., tk.Widget]

    class Config:
        arbitrary_types_allowed = True
