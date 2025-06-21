# storybook/context.py - StoryContext 実装
"""StoryFactory に渡すコンテキストオブジェクト。"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, List, Sequence, Type

from pydantic import BaseModel

from pubsubtk.storybook.meta import KnobSpec
from pubsubtk.storybook.variable_manager import get_variable_manager


class StoryContext(BaseModel):
    """ストーリー実行時に渡されるコンテキスト"""

    parent: tk.Widget
    _knob_specs: List[KnobSpec] = []
    _publish_callback: Callable[[str, dict], None] | None = None

    class Config:
        arbitrary_types_allowed = True

    def set_publish_callback(self, callback: Callable[[str, dict], None]) -> None:
        """PubSub発行用のコールバックを設定"""
        self._publish_callback = callback

    def knob(
        self,
        *,
        name: str,
        type: Type,
        default: Any,
        desc: str = "",
        range: Sequence[Any] | None = None,
        choices: List[str] | None = None,
        multiline: bool = False,
    ) -> tk.Variable:
        """Knob を宣言し tk.Variable を返す。"""

        spec = KnobSpec(
            name=name,
            type=type,
            default=default,
            desc=desc,
            range=tuple(range) if range else None,
            choices=choices,
            multiline=multiline,
        )
        self._knob_specs.append(spec)

        # VariableManagerから共有変数を取得
        var_manager = get_variable_manager()
        return var_manager.create_or_get_variable(spec)

    def publish(self, topic: str, **kwargs: Any) -> None:
        """Story 空間向け PubSub 発火（名前空間前置き）。"""
        if self._publish_callback:
            self._publish_callback(f"storybook.{topic}", kwargs)

    def on_change(self, var: tk.Variable, cb: Callable[[Any], None]) -> None:
        """tk.Variable にトレーサを張って変更をフック。"""

        def _update(*_):
            cb(var.get())

        var.trace_add("write", _update)

    @property
    def knob_specs(self) -> List[KnobSpec]:
        """宣言済み KnobSpec 一覧"""
        return self._knob_specs
