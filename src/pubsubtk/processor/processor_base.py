from typing import Dict, Type, TypeVar

from pubsubtk.core.pubsub_base import PubSubBase

ProcessorBase = PubSubBase

_processors: Dict[str, ProcessorBase] = {}

P = TypeVar("P", bound=ProcessorBase)


def register_processor(name: str, proc: Type[P]) -> None:
    """
    プロセッサを名前で登録する。

    - ProcessorはUIや他ProcessorからのPubSubイベントを購読し、
      状態更新や副作用処理を一元的に担う役割を持つ。
    - store.update_state(store.state.foo, ...) のようなパスプロキシを使うことで、
      どのProcessorがどの状態を更新しているかIDEで追跡しやすく、
      大規模開発でも責務分離・可読性・保守性が高まる。

    Args:
        name: プロセッサ名
        proc: ProcessorBaseを継承したクラス
    Raises:
        KeyError: 既に同名のプロセッサが登録済みの場合
    """
    if name in _processors:
        raise KeyError(f"Processor '{name}' is already registered.")
    _processors[name] = proc


def delete_processor(name: str) -> None:
    """
    登録済みプロセッサを削除し、teardown()を呼び出す。

    Args:
        name: プロセッサ名
    Raises:
        KeyError: 指定名のプロセッサが未登録の場合
    """
    if name not in _processors:
        raise KeyError(f"Processor '{name}' not found.")
    _processors[name].teardown()
    del _processors[name]
