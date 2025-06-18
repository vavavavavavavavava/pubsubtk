# storybook/meta.py - Story/Knob メタモデル
"""StoryMeta / KnobSpec を定義するモジュール。"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, List, Type

from pydantic import BaseModel, Field


class KnobSpec(BaseModel):
    """Knob（動的プロパティ）の仕様"""

    name: str
    type_: Type = Field(..., alias="type")
    default: Any
    desc: str = ""
    range: tuple[Any, Any, Any] | None = None
    choices: List[str] | None = None
    multiline: bool = False
    var: tk.Variable  # 実際の tk.Variable

    class Config:
        arbitrary_types_allowed = True


class StoryMeta(BaseModel):
    """Story のメタ情報"""

    id: str
    path: List[str]  # ["Button", "Primary"]
    title: str  # "Primary"
    factory: Callable[..., tk.Widget]

    class Config:
        arbitrary_types_allowed = True
