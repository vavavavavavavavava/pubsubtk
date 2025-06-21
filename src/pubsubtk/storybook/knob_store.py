# storybook/knob_store.py
"""Knob値のグローバル保存ストア"""

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .knob.knob_types import KnobValue


class KnobStore:
    """Knob値をストーリー間で永続化するグローバルストア"""
    
    def __init__(self):
        # {story_id: {knob_name: value}}
        self._values: Dict[str, Dict[str, Any]] = {}
        # {story_id: {knob_name: KnobValue}}
        self._knob_instances: Dict[str, Dict[str, "KnobValue"]] = {}
    
    def get_value(self, story_id: str, knob_name: str, default: Any = None) -> Any:
        """保存されたknob値を取得"""
        return self._values.get(story_id, {}).get(knob_name, default)
    
    def set_value(self, story_id: str, knob_name: str, value: Any) -> None:
        """knob値を保存"""
        if story_id not in self._values:
            self._values[story_id] = {}
        self._values[story_id][knob_name] = value
    
    def get_knob_instance(self, story_id: str, knob_name: str) -> Optional["KnobValue"]:
        """KnobValueインスタンスを取得"""
        return self._knob_instances.get(story_id, {}).get(knob_name)
    
    def set_knob_instance(self, story_id: str, knob_name: str, knob_value: "KnobValue") -> None:
        """KnobValueインスタンスを保存"""
        if story_id not in self._knob_instances:
            self._knob_instances[story_id] = {}
        self._knob_instances[story_id][knob_name] = knob_value
    
    def get_all_knobs(self, story_id: str) -> Dict[str, "KnobValue"]:
        """指定ストーリーの全KnobValueを取得"""
        return self._knob_instances.get(story_id, {})
    
    def clear_story(self, story_id: str) -> None:
        """指定ストーリーのknob値をクリア"""
        self._values.pop(story_id, None)
        self._knob_instances.pop(story_id, None)


# グローバルインスタンス
_knob_store = KnobStore()


def get_knob_store() -> KnobStore:
    """グローバルKnobStoreを取得"""
    return _knob_store