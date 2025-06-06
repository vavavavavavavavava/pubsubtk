# processor_base.py - Processor の基底クラス

"""ビジネスロジックを担う Processor 用の抽象基底クラス。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

from pubsubtk.core.default_topic_base import PubSubDefaultTopicBase
from pubsubtk.store.store import Store

TState = TypeVar("TState", bound=BaseModel)


class ProcessorBase(PubSubDefaultTopicBase, Generic[TState]):
    """Processor の基底クラス。"""

    def __init__(self, store: Store[TState], *args, **kwargs) -> None:
        """Store を受け取って初期化します。"""

        # 型引数付きの Store[TState] を取得
        self.store: Store[TState] = store

        super().__init__(*args, **kwargs)

