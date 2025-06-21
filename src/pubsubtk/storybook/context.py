# storybook/context.py - StoryContext 実装
"""StoryFactory に渡すコンテキストオブジェクト。"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union

from pydantic import BaseModel
from pubsubtk.storybook.knob.knob_types import KnobSpec, KnobValue
from pubsubtk.storybook.knob_store import get_knob_store



class StoryContext(BaseModel):
    """ストーリー実行時に渡されるコンテキスト"""

    parent: tk.Widget
    _publish_callback: Callable[[str, dict], None] | None = None
    _knob_values: Dict[str, KnobValue] = {}
    _story_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def set_publish_callback(self, callback: Callable[[str, dict], None]) -> None:
        """PubSub発行用のコールバックを設定"""
        self._publish_callback = callback
    
    def set_story_id(self, story_id: str) -> None:
        """ストーリーIDを設定（値の永続化用）"""
        self._story_id = story_id
    
    def knob(self, name: str, type_: Type, default: Any, 
             desc: str = "", range_: Optional[tuple] = None, 
             choices: Optional[List[str]] = None, multiline: bool = False) -> KnobValue:
        """Knobを宣言してKnobValueオブジェクトを返す（値の永続化あり）"""
        
        store = get_knob_store()
        story_id = self._story_id or "default"
        
        # グローバルストアから既存のKnobValueを取得
        existing_knob = store.get_knob_instance(story_id, name)
        if existing_knob:
            self._knob_values[name] = existing_knob
            return existing_knob
        
        # 新しいKnobSpec作成
        spec = KnobSpec(
            name=name,
            type=type_,
            default=default,
            desc=desc,
            range=range_,
            choices=choices,
            multiline=multiline
        )
        
        # 保存された値があれば使用、なければデフォルト値
        saved_value = store.get_value(story_id, name, default)
        
        # KnobValue作成
        knob_value = KnobValue(spec, saved_value)
        
        # 値変更時のコールバックを追加（グローバルストアに保存）
        knob_value.add_change_callback(
            lambda value: store.set_value(story_id, name, value)
        )
        
        # ローカルおよびグローバルストアに保存
        self._knob_values[name] = knob_value
        store.set_knob_instance(story_id, name, knob_value)
        
        return knob_value
    
    @property
    def knob_values(self) -> Dict[str, KnobValue]:
        """登録済みKnobValue一覧"""
        return self._knob_values
    
    def clear_knobs(self):
        """Knobをクリア（ストーリー切り替え時）"""
        self._knob_values.clear()


    def publish(self, topic: str, **kwargs: Any) -> None:
        """Story 空間向け PubSub 発火（名前空間前置き）。"""
        if self._publish_callback:
            self._publish_callback(f"storybook.{topic}", kwargs)

    def on_change(self, var: tk.Variable, cb: Callable[[Any], None]) -> None:
        """tk.Variable にトレーサを張って変更をフック。"""

        def _update(*_):
            cb(var.get())

        var.trace_add("write", _update)

