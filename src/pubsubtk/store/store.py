# store.py - アプリケーション状態を管理するクラス

"""Pydantic モデルを用いた型安全な状態管理を提供します。"""

from typing import Any, Generic, Optional, Type, TypeVar, cast

from pubsub import pub
from pydantic import BaseModel

from pubsubtk.core.pubsub_base import PubSubBase
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
        """StateProxy を初期化する。

        Args:
            store: 値を参照する対象 ``Store``。
            path: 現在のパス文字列。
        """

        self._store = store
        self._path = path

    def __getattr__(self, name: str) -> "StateProxy[TState]":
        """属性アクセスを連結した ``StateProxy`` を返す。"""

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
        """パス文字列を返す。"""

        return f"{self._path}"

    __str__ = __repr__


class Store(PubSubBase, Generic[TState]):
    """
    型安全な状態管理を提供するジェネリックなStoreクラス。

    - Pydanticモデルを状態として保持し、状態操作を提供
    - get_current_state()で状態のディープコピーを取得
    - update_state()/add_to_list()で状態を更新し、PubSubで通知
    - create_partial_state_updater()で部分更新用関数を生成
    - `store.state.count` のようなパスプロキシを使うことで、
      `store.update_state(store.state.count, 1)` のようにIDEの「定義へ移動」や補完機能を活用しつつ、
      状態更新のパスを安全・明示的に指定できる（従来の文字列パス指定の弱点を解消）
    """

    def __init__(self, initial_state_class: Type[TState]):
        """Store を初期化する。

        Args:
            initial_state_class: 管理対象となる ``BaseModel`` のサブクラス。
        """
        self._state_class = initial_state_class
        self._state = initial_state_class()
        
        # PubSubBase.__init__()を呼び出して購読設定を有効化
        super().__init__()

    def setup_subscriptions(self):
        self.subscribe(DefaultUpdateTopic.UPDATE_STATE, self.update_state)
        self.subscribe(DefaultUpdateTopic.ADD_TO_LIST, self.add_to_list)

    @property
    def state(self) -> TState:
        """
        状態への動的パスアクセス用プロキシを返す。
        """
        return cast(TState, StateProxy(self))

    def get_current_state(self) -> TState:
        """
        現在の状態のディープコピーを返す。
        """
        return self._state.model_copy(deep=True)

    def update_state(self, state_path: str, new_value: Any) -> None:
        """指定パスの属性を更新し、変更通知を送信する。

        Args:
            state_path: 変更対象の属性パス（例: ``"foo.bar"``）。
            new_value: 新しく設定する値。
        """
        target_obj, attr_name, old_value = self._resolve_path(str(state_path))

        # 新しい値を設定する前に型チェック
        self._validate_and_set_value(target_obj, attr_name, new_value)

        self.publish(
            f"{DefaultUpdateTopic.STATE_CHANGED}.{state_path}",
            old_value=old_value,
            new_value=new_value,
        )

    def add_to_list(self, state_path: str, item: Any) -> None:
        """リスト属性に要素を追加し、追加通知を送信する。

        Args:
            state_path: 追加先となるリストの属性パス。
            item: 追加する要素。
        """
        target_obj, attr_name, current_list = self._resolve_path(str(state_path))

        if not isinstance(current_list, list):
            raise TypeError(f"Property at '{state_path}' is not a list")

        # リストをコピーして新しい要素を追加
        new_list = current_list.copy()
        new_list.append(item)

        # 新しいリストで更新
        self._validate_and_set_value(target_obj, attr_name, new_list)
        
        index = len(new_list) - 1

        pub.sendMessage(
            f"{DefaultUpdateTopic.STATE_ADDED}.{state_path}",
            item=item,
            index=index,
        )

    def _resolve_path(self, path: str) -> tuple[Any, str, Any]:
        """
        属性パスを解決し、対象オブジェクト・属性名・現在値を返す。

        Args:
            path: 解析する属性パス。
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
        """属性値を型検証してから設定する。"""
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
_store: Optional[Store[Any]] = None


def get_store(state_cls: Type[TState]) -> Store[TState]:
    """グローバルな ``Store`` インスタンスを取得する。

    Args:
        state_cls: ``Store`` 生成に使用する状態モデルの型。

    Returns:
        共有 ``Store`` インスタンス。

    Raises:
        RuntimeError: 既に別の ``state_cls`` で生成されている場合。
    """
    global _store
    if _store is None:
        _store = Store(state_cls)
    else:
        existing = getattr(_store, "_state_class", None)
        if existing is not state_cls:
            raise RuntimeError(
                f"Store は既に {existing!r} で生成されています（呼び出し時の state_cls={state_cls!r}）"
            )
    return cast(Store[TState], _store)
