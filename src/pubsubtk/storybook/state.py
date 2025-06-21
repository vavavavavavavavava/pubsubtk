# storybook/state.py - Pydantic 状態モデル
"""Storybook 用の状態オブジェクト。"""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class StorybookState(BaseModel):
    """Storybook の状態を一元管理するモデル"""

    active_story_id: Optional[str] = None
    layout_mode: str = "normal"  # "normal" or "fullscreen"
    knob_values: Dict[str, Any] = {}  # Knob値の保存（ストーリー間で共有）
