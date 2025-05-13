# core/api.py

from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel

from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.core.store import Store

# Store で使っている TState をここでも再定義
TState = TypeVar("TState", bound=BaseModel)
P = TypeVar("P", bound=PubSubBase)

# 実体としてはどんな State 型でも格納できるので Any
_store: Optional[Store[Any]] = None
_processors: Dict[str, PubSubBase] = {}


def create_store(state: Type[TState]) -> Store[TState]:
    """
    初期状態 state を受け取って Store[TState] を生成します。
    既に _store がセットされている場合はエラー。
    """
    global _store
    if _store is not None:
        raise RuntimeError("Store is already created. Call get_store() instead.")
    _store = Store(state)
    return _store  # 型引数付き Store[TState] と推論されます


def get_store() -> Store[Any]:
    """
    既存の Store を返します。未生成ならエラー。
    """
    if _store is None:
        raise RuntimeError("Store is not created yet. Call create_store(state) first.")
    return _store


def register_processor(name: str, proc: Type[P]) -> None:
    if name in _processors:
        raise KeyError(f"Processor '{name}' is already registered.")
    _processors[name] = proc


def delete_processor(name: str) -> None:
    if name not in _processors:
        raise KeyError(f"Processor '{name}' not found.")
    _processors[name].teardown()
    del _processors[name]
