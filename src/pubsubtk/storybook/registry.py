# storybook/registry.py - StoryRegistry
"""Story を保管・列挙するシングルトンレジストリ。"""

from __future__ import annotations

from typing import List

from .meta import StoryMeta


class StoryRegistry:
    """ストーリーメタを管理するレジストリ"""

    _stories: List[StoryMeta] = []

    @classmethod
    def register(cls, meta: StoryMeta) -> None:
        cls._stories.append(meta)

    @classmethod
    def list(cls) -> List[StoryMeta]:
        return cls._stories.copy()

    @classmethod
    def clear(cls) -> None:
        """テスト用などでレジストリをクリア"""
        cls._stories.clear()
