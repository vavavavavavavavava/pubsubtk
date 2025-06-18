# storybook/meta.py - Story/Knob メタモデル
"""
src/pubsubtk/storybook/meta.py

StoryMeta と KnobSpec を定義するモジュール。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, List, Type

from pydantic import BaseModel, Field, PrivateAttr


class KnobSpec(BaseModel):
    """Knob（動的プロパティ）の仕様"""

    name: str
    type_: Type = Field(..., alias="type")
    default: Any
    desc: str = ""
    range: tuple[Any, Any, Any] | None = None
    choices: List[str] | None = None
    multiline: bool = False
    _var: tk.Variable = PrivateAttr()

    def __init__(self, *, var: tk.Variable, **data: Any):
        """``tk.Variable`` を ``PrivateAttr`` として保持する。"""
        super().__init__(**data)
        self._var = var

    @property
    def var(self) -> tk.Variable:
        """保持している ``tk.Variable`` を返す。"""
        return self._var

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
