from threading import Lock
from typing import Any, Generic, Optional, Type, TypeVar, cast

from pubsub import pub
from pydantic import BaseModel

from pubsubtk.topic.topics import DefaultUpdateTopic

TState = TypeVar("TState", bound=BaseModel)


class StateProxy(Generic[TState]):
    """
    Storeのstate属性に対する動的なパスアクセスを提供するプロキシ。

    - store.state.foo.bar のようなドット記法でネスト属性へアクセス可能
    - 存在しない属性アクセス時は AttributeError を送出
    - __repr__ でパス文字列を返す
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
    型安全な状態管理を提供するジェネリックなStoreクラス。

    - Pydanticモデルを状態として保持し、スレッドセーフに操作
    - get_current_state()で状態のディープコピーを取得
    - update_state()/add_to_list()で状態を更新し、PubSubで通知
    - create_partial_state_updater()で部分更新用関数を生成
    - `store.state.count` のようなパスプロキシを使うことで、
      `store.update_state(store.state.count, 1)` のようにIDEの「定義へ移動」や補完機能を活用しつつ、
      状態更新のパスを安全・明示的に指定できる（従来の文字列パス指定の弱点を解消）
    """

    def __init__(self, initial_state_class: Type[TState]):
        """
        Storeを初期化する。

        Args:
            initial_state_class: Pydanticモデルの型
        """
        self._state_class = initial_state_class
        self._state = initial_state_class()
        self._lock = Lock()
        self._version: int = 0
        self._cached_state: Optional[TState] = None
        self._cached_version: int = -1

    @property
    def state(self) -> TState:
        """
        状態への動的パスアクセス用プロキシを返す。
        """
        return cast(TState, StateProxy(self))

    def get_current_state(self) -> TState:
        """
        現在の状態のディープコピーを返す。キャッシュを利用。
        """
        with self._lock:
            if self._cached_state is None or self._cached_version != self._version:
                self._cached_state = self._state.model_copy(deep=True)
                self._cached_version = self._version
            return self._cached_state

    def update_state(self, path: str, new_value: Any) -> None:
        """
        指定パスの属性を新しい値で更新し、PubSubで変更通知を送信する。

        Args:
            path: 属性パス（例: "foo.bar"）
            new_value: 新しい値
        """
        with self._lock:
            target_obj, attr_name, old_value = self._resolve_path(path)

            # 新しい値を設定する前に型チェック
            self._validate_and_set_value(target_obj, attr_name, new_value)
            self._version += 1

        pub.sendMessage(
            f"{DefaultUpdateTopic.STATE_CHANGED}.{path}",
            old_value=old_value,
            new_value=new_value,
        )

    def add_to_list(self, path: str, item: Any) -> None:
        """
        指定パスのリスト属性に要素を追加し、PubSubで追加通知を送信する。

        Args:
            path: 属性パス
            item: 追加する要素
        """
        with self._lock:
            target_obj, attr_name, current_list = self._resolve_path(path)

            if not isinstance(current_list, list):
                raise TypeError(f"Property at '{path}' is not a list")

            # リストをコピーして新しい要素を追加
            new_list = current_list.copy()
            new_list.append(item)

            # 新しいリストで更新
            self._validate_and_set_value(target_obj, attr_name, new_list)
            self._version += 1
            index = len(new_list) - 1

        pub.sendMessage(
            f"{DefaultUpdateTopic.STATE_ADDED}.{path}",
            item=item,
            index=index,
        )

    def _resolve_path(self, path: str) -> tuple[Any, str, Any]:
        """
        属性パスを解決し、対象オブジェクト・属性名・現在値を返す。

        Args:
            path: 属性パス
        Returns:
            (対象オブジェクト, 属性名, 現在値)
        """
        segments = path.split(".")

        if not segments:
            raise ValueError("Empty path")

        # 最後のセグメントを取り出し
        attr_name = segments[-1]

        # 最後のセグメント以外のパスをたどって対象オブジェクトを取得
        current = self._state
        for segment in segments[:-1]:
            if not hasattr(current, segment):
                raise AttributeError(f"No such attribute: {segment} in path {path}")
            current = getattr(current, segment)

        # 現在の値を取得
        if not hasattr(current, attr_name):
            raise AttributeError(f"No such attribute: {attr_name} in path {path}")

        old_value = getattr(current, attr_name)
        return current, attr_name, old_value

    def _validate_and_set_value(
        self, target_obj: Any, attr_name: str, new_value: Any
    ) -> None:
        """
        属性値を型検証し、設定する。
        """
        # Pydanticモデルの場合、フィールドの型情報を取得
        if isinstance(target_obj, BaseModel):
            model_fields = target_obj.model_fields

            if attr_name in model_fields:
                field_info = model_fields[attr_name]

                # もし新しい値がPydanticモデルの場合、model_validateを使用
                if hasattr(new_value, "model_dump") and hasattr(
                    field_info.annotation, "model_validate"
                ):
                    field_type = field_info.annotation
                    validated_value = field_type.model_validate(new_value)
                    setattr(target_obj, attr_name, validated_value)
                    return

        # 通常の属性設定
        setattr(target_obj, attr_name, new_value)

    def create_partial_state_updater(self, base_path: str):
        """
        指定パス以下の部分更新用関数を生成する。

        Args:
            base_path: 基準パス
        Returns:
            サブパスと値を受けてupdate_stateする関数
        """

        def updater(sub_path: str, value: Any):
            full_path = f"{base_path}.{sub_path}" if base_path else sub_path
            self.update_state(full_path, value)

        return updater


# 実体としてはどんな State 型でも格納できるので Any
_store: Optional[Store[TState]] = None


def create_store(state: Type[TState]) -> Store[TState]:
    """
    Storeインスタンスを生成し、グローバルに登録する。

    Args:
        state: Pydanticモデルの型
    Returns:
        Store[TState]インスタンス
    Raises:
        RuntimeError: 既にStoreが生成済みの場合
    """
    global _store
    if _store is not None:
        raise RuntimeError("Store is already created. Call get_store() instead.")
    _store = Store(state)
    return _store  # 型引数付き Store[TState] と推論されます


def get_store() -> Store[Any]:
    """
    既存のStoreインスタンスを返す。

    Returns:
        Store[Any]インスタンス
    Raises:
        RuntimeError: Storeが未生成の場合
    """
    if _store is None:
        raise RuntimeError("Store is not created yet. Call create_store(state) first.")
    return _store
