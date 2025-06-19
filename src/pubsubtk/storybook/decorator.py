# storybook/decorator.py - @story デコレータ
"""ストーリーを登録するためのデコレータ。"""

from __future__ import annotations

import re
from typing import Callable

from pubsubtk.storybook.meta import StoryMeta
from pubsubtk.storybook.registry import StoryRegistry


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", text.lower())


def story(path: str | None = None, title: str | None = None):
    """Story 登録用デコレータ。

    Args:
        path: "Button.Primary" のようなドット区切り階層。
        title: 葉ノード名。省略時は path の末尾が使われる。
    """

    def decorator(factory: Callable):
        # デフォルトパス = <ReturnClass>.<func_name>
        comp_name = getattr(factory, "__name__", "Component")
        default_path = f"{comp_name}.{factory.__name__}"

        full_path = (path or default_path).strip(".")
        segments = full_path.split(".")
        leaf_title = title or segments[-1]

        meta = StoryMeta(
            id=_slugify(full_path),
            path=segments[:-1],
            title=leaf_title,
            factory=factory,
        )
        StoryRegistry.register(meta)
        return factory

    return decorator
