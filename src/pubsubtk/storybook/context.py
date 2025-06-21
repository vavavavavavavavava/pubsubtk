# storybook/context.py - StoryContext 実装
"""StoryFactory に渡すコンテキストオブジェクト。"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, List, Sequence, Type

from pydantic import BaseModel



class StoryContext(BaseModel):
    """ストーリー実行時に渡されるコンテキスト"""

    parent: tk.Widget
    _publish_callback: Callable[[str, dict], None] | None = None

    class Config:
        arbitrary_types_allowed = True

    def set_publish_callback(self, callback: Callable[[str, dict], None]) -> None:
        """PubSub発行用のコールバックを設定"""
        self._publish_callback = callback


    def publish(self, topic: str, **kwargs: Any) -> None:
        """Story 空間向け PubSub 発火（名前空間前置き）。"""
        if self._publish_callback:
            self._publish_callback(f"storybook.{topic}", kwargs)

    def on_change(self, var: tk.Variable, cb: Callable[[Any], None]) -> None:
        """tk.Variable にトレーサを張って変更をフック。"""

        def _update(*_):
            cb(var.get())

        var.trace_add("write", _update)

