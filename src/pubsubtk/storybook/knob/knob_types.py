# storybook/knob/knob_types.py
"""Knobの型定義とデータクラス"""

from __future__ import annotations

from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class KnobSpec(BaseModel):
    """Knobの仕様定義"""
    
    name: str
    type_: type = Field(..., alias="type")
    default: Any
    desc: str = ""
    range_: Optional[tuple[Union[int, float], Union[int, float]]] = Field(None, alias="range")
    choices: Optional[List[str]] = None
    multiline: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class KnobValue:
    """Knob値の動的オブジェクト（Story内で使用）"""
    
    def __init__(self, spec: KnobSpec, initial_value: Any = None):
        self.spec = spec
        self._value = initial_value if initial_value is not None else spec.default
        self._callbacks: List[callable] = []
    
    @property
    def value(self) -> Any:
        """現在の値を取得"""
        return self._value
    
    @value.setter
    def value(self, new_value: Any) -> None:
        """値を設定し、コールバックを実行"""
        if self._value != new_value:
            self._value = new_value
            for callback in self._callbacks:
                callback(new_value)
    
    def add_change_callback(self, callback: callable) -> None:
        """値変更時のコールバックを追加"""
        self._callbacks.append(callback)
    
    def __str__(self) -> str:
        return str(self._value)
    
    def __repr__(self) -> str:
        return f"KnobValue({self.spec.name}={self._value})"