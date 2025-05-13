from threading import Lock
from typing import Any, Generic, Optional, TypeVar, cast

from pubsub import pub
from pydantic import BaseModel

from pubsubtk.core.topics import DefaultUpdateTopic

TState = TypeVar("TState", bound=BaseModel)


class StateProxy(Generic[TState]):
    """
    動的にパスをつなげる Proxy。
    __getattr__ で new_path を構築し、__repr__ で文字列化。
    存在チェックは get_current_state() を使って行う。
    """

    def __init__(self, store: "Store[TState]", path: str = ""):
        self._store = store
        self._path = path

    def __getattr__(self, name: str) -> "StateProxy[TState]":
        new_path = f"{self._path}.{name}" if self._path else name

        # 存在チェック：TState モデルに new_path が通るか確認
        cur = self._store.get_current_state()
        for seg in new_path.split("."):
            if hasattr(cur, seg):
                cur = getattr(cur, seg)
            else:
                raise AttributeError(f"No such property: store.state.{new_path}")

        return StateProxy(self._store, new_path)

    def __repr__(self) -> str:
        return f"store.state.{self._path}"

    __str__ = __repr__


class Store(Generic[TState]):
    """
    ジェネリック化した Store。
    ・get_current_state(): Pydantic の model_copy(deep=True) で深いコピーを返し、
      version が変わっていなければキャッシュを返す。
    ・update_state()/add_to_list(): lock 内で状態更新＋version インクリメント。
    """

    def __init__(self, initial_state: TState):
        self._state: TState = initial_state
        self._lock = Lock()
        self._version: int = 0
        self._cached_state: Optional[TState] = None
        self._cached_version: int = -1

    @property
    def state(self) -> StateProxy[TState]:
        return cast(StateProxy[TState], StateProxy(self))

    def get_current_state(self) -> TState:
        """
        深いコピーを返す（Pydantic v2 の model_copy を利用）。
        キャッシュのバージョンが最新なら前回のコピーを返す。
        """
        with self._lock:
            if self._cached_state is None or self._cached_version != self._version:
                self._cached_state = self._state.model_copy(deep=True)
                self._cached_version = self._version
            return self._cached_state  # type: ignore

    def update_state(self, path: str, new_value: Any) -> None:
        """
        path で指定したプロパティを更新し、version をインクリメント。
        topic 通知も行う。
        """
        with self._lock:
            old = self._get_by_path(path)
            self._set_by_path(path, new_value)
            self._version += 1

        pub.sendMessage(
            f"{DefaultUpdateTopic.STATE_CHANGED}.{path}",
            old_value=old,
            new_value=new_value,
        )

    def add_to_list(self, path: str, item: Any) -> None:
        """
        path で指定したリストに要素を追加し、version をインクリメント。
        topic 通知も行う。
        """
        with self._lock:
            old_list = self._get_by_path(path) or []
            new_list = old_list + [item]
            self._set_by_path(path, new_list)
            self._version += 1
            index = len(new_list) - 1

        pub.sendMessage(
            f"{DefaultUpdateTopic.STATE_ADDED}.{path}",
            item=item,
            index=index,
        )

    def _get_by_path(self, path: str) -> Any:
        data = self._state.model_dump()
        cur = data
        for key in path.split("."):
            if isinstance(cur, dict):
                cur = cur.get(key)
            else:
                return None
        return cur

    def _set_by_path(self, path: str, val: Any) -> None:
        data = self._state.model_dump()
        parts = path.split(".")
        node = data
        for k in parts[:-1]:
            node = node.setdefault(k, {})
        node[parts[-1]] = val.model_dump() if hasattr(val, "model_dump") else val
        # 型を維持して再構築
        self._state = type(self._state).model_validate(data)
