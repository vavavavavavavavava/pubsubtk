# store.py - アプリケーション状態を管理するクラス

"""
src/pubsubtk/store/store.py

Pydantic モデルを用いた型安全な状態管理を提供します。
"""

import copy
from collections import defaultdict
from typing import Any, Generic, Optional, Type, TypeVar, cast

from pydantic import BaseModel

from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.topic.topics import DefaultUndoTopic, DefaultUpdateTopic

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
    - update_state()/add_to_list()/add_to_dict()で状態を更新し、PubSubで通知
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

        # Undo/Redo 履歴管理用フィールド
        self._undo_enabled: set[str] = set()  # 追跡対象パス
        self._undo_stacks: dict[str, list] = defaultdict(list)  # パス別Undoスタック
        self._redo_stacks: dict[str, list] = defaultdict(list)  # パス別Redoスタック
        self._max_histories: dict[str, int] = {}  # パス別履歴上限
        self._during_ur_op: bool = False  # Undo/Redo操作中の再帰抑制フラグ

        # PubSubBase.__init__()を呼び出して購読設定を有効化
        super().__init__()

    def setup_subscriptions(self):
        # 既存の状態更新系トピック
        self.subscribe(DefaultUpdateTopic.UPDATE_STATE, self.update_state)
        self.subscribe(DefaultUpdateTopic.REPLACE_STATE, self.replace_state)
        self.subscribe(DefaultUpdateTopic.ADD_TO_LIST, self.add_to_list)
        self.subscribe(DefaultUpdateTopic.ADD_TO_DICT, self.add_to_dict)

        # Undo/Redo系トピック
        self.subscribe(DefaultUndoTopic.ENABLE_UNDO_REDO, self._enable_undo_redo)
        self.subscribe(DefaultUndoTopic.DISABLE_UNDO_REDO, self._disable_undo_redo)
        self.subscribe(DefaultUndoTopic.UNDO, self._undo)
        self.subscribe(DefaultUndoTopic.REDO, self._redo)

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

    def replace_state(self, new_state: TState) -> None:
        """状態オブジェクト全体を置き換え、全フィールドに変更通知を送信する。

        Args:
            new_state: 新しい状態オブジェクト。
        """
        if not isinstance(new_state, self._state_class):
            raise TypeError(f"new_state must be an instance of {self._state_class}")

        old_state = self._state
        self._state = new_state.model_copy(deep=True)

        # 全フィールドに変更通知を送信
        for field_name in self._state_class.model_fields.keys():
            old_value = getattr(old_state, field_name)
            new_value = getattr(self._state, field_name)

            self.publish(
                f"{DefaultUpdateTopic.STATE_CHANGED}.{field_name}",
                old_value=old_value,
                new_value=new_value,
            )
            self.publish(f"{DefaultUpdateTopic.STATE_UPDATED}.{field_name}")

    def update_state(self, state_path: str, new_value: Any) -> None:
        """指定パスの属性を更新し、変更通知を送信する。

        Args:
            state_path: 変更対象の属性パス（例: ``"foo.bar"``）。
            new_value: 新しく設定する値。
        """
        target_obj, attr_name, old_value = self._resolve_path(str(state_path))

        # Undo履歴をキャプチャ（既存の値を記録）
        self._capture_for_undo(str(state_path), old_value)

        # 新しい値を設定する前に型チェック
        self._validate_and_set_value(target_obj, attr_name, new_value)

        # 詳細な変更通知（old_value, new_valueを含む）
        self.publish(
            f"{DefaultUpdateTopic.STATE_CHANGED}.{state_path}",
            old_value=old_value,
            new_value=new_value,
        )

        # シンプルな更新通知（引数なし）
        self.publish(f"{DefaultUpdateTopic.STATE_UPDATED}.{state_path}")

    def add_to_list(self, state_path: str, item: Any) -> None:
        """リスト属性に要素を追加し、追加通知を送信する。

        Args:
            state_path: 追加先となるリストの属性パス。
            item: 追加する要素。
        """
        target_obj, attr_name, current_list = self._resolve_path(str(state_path))

        if not isinstance(current_list, list):
            raise TypeError(f"Property at '{state_path}' is not a list")

        # Undo履歴をキャプチャ（既存のリストを記録）
        self._capture_for_undo(str(state_path), current_list)

        # リストをコピーして新しい要素を追加
        new_list = current_list.copy()
        new_list.append(item)

        # 新しいリストで更新
        self._validate_and_set_value(target_obj, attr_name, new_list)

        index = len(new_list) - 1

        self.publish(
            f"{DefaultUpdateTopic.STATE_ADDED}.{state_path}",
            item=item,
            index=index,
        )

        # リスト追加でも更新通知を送信
        self.publish(f"{DefaultUpdateTopic.STATE_UPDATED}.{state_path}")

    def add_to_dict(self, state_path: str, key: str, value: Any) -> None:
        """辞書属性に要素を追加し、追加通知を送信する。

        Args:
            state_path: 追加先となる辞書の属性パス。
            key: 追加するキー。
            value: 追加する値。
        """
        target_obj, attr_name, current_dict = self._resolve_path(str(state_path))

        if not isinstance(current_dict, dict):
            raise TypeError(f"Property at '{state_path}' is not a dict")

        # Undo履歴をキャプチャ（既存の辞書を記録）
        self._capture_for_undo(str(state_path), current_dict)

        new_dict = current_dict.copy()
        new_dict[key] = value

        self._validate_and_set_value(target_obj, attr_name, new_dict)

        self.publish(
            f"{DefaultUpdateTopic.DICT_ADDED}.{state_path}",
            key=key,
            value=value,
        )

        # 辞書追加でも更新通知を送信
        self.publish(f"{DefaultUpdateTopic.STATE_UPDATED}.{state_path}")

    # --- Undo/Redo 履歴管理機能 ---

    def _enable_undo_redo(self, state_path: str, max_history: int = 10) -> None:
        """指定パスのUndo/Redo機能を有効化し、現在の値を初期スナップショットとして記録する。

        Args:
            state_path: 追跡対象の状態パス
            max_history: 保持する履歴の最大数（デフォルト: 10）
        """
        self._undo_enabled.add(state_path)
        self._max_histories[state_path] = max_history

        # 現在の値を初期スナップショットとして記録
        try:
            _, _, current_value = self._resolve_path(state_path)
            self._undo_stacks[state_path] = [copy.deepcopy(current_value)]
            self._redo_stacks[state_path].clear()
        except (AttributeError, ValueError):
            # パスが存在しない場合は空の履歴で開始
            self._undo_stacks[state_path] = []
            self._redo_stacks[state_path].clear()

        # ステータス通知を送信
        self._emit_ur_status(state_path)

    def _disable_undo_redo(self, state_path: str) -> None:
        """指定パスのUndo/Redo機能を無効化し、履歴データを削除する。

        Args:
            state_path: 無効化する状態パス
        """
        self._undo_enabled.discard(state_path)
        self._undo_stacks.pop(state_path, None)
        self._redo_stacks.pop(state_path, None)
        self._max_histories.pop(state_path, None)

    def _capture_for_undo(self, state_path: str, old_value: Any) -> None:
        """状態変更前に古い値をUndo履歴に記録する。

        Args:
            state_path: 変更対象の状態パス
            old_value: 変更前の値
        """
        # Undo/Redo対象でない、またはUndo/Redo操作中の場合はスキップ
        if state_path not in self._undo_enabled or self._during_ur_op:
            return

        stack = self._undo_stacks[state_path]
        stack.append(copy.deepcopy(old_value))

        # 履歴上限の管理
        max_len = self._max_histories.get(state_path, 10)
        if len(stack) > max_len:
            stack.pop(0)  # 最古の履歴を削除

        # 新しい変更が発生したのでRedo履歴をクリア
        self._redo_stacks[state_path].clear()

        # ステータス通知を送信
        self._emit_ur_status(state_path)

    def _undo(self, state_path: str) -> None:
        """指定パスの状態を1つ前の値に戻す。

        Args:
            state_path: Undoを実行する状態パス
        """
        if state_path not in self._undo_enabled:
            return

        undo_stack = self._undo_stacks[state_path]
        if len(undo_stack) < 2:  # 現在値 + 少なくとも1つの履歴が必要
            return

        # 現在の値をRedo履歴に保存
        try:
            _, _, current_value = self._resolve_path(state_path)
            self._redo_stacks[state_path].append(copy.deepcopy(current_value))
        except (AttributeError, ValueError):
            return

        # 最新の履歴値を取得（現在値の1つ前）
        self._during_ur_op = True  # 再帰防止フラグを設定
        try:
            undo_stack.pop()  # 現在値を削除
            previous_value = undo_stack[-1]  # 1つ前の値を取得（スタックには残す）
            self.update_state(state_path, previous_value)
        finally:
            self._during_ur_op = False

        # ステータス通知を送信
        self._emit_ur_status(state_path)

    def _redo(self, state_path: str) -> None:
        """指定パスのUndoを取り消し、Redoを実行する。

        Args:
            state_path: Redoを実行する状態パス
        """
        if state_path not in self._undo_enabled:
            return

        redo_stack = self._redo_stacks[state_path]
        if not redo_stack:
            return

        # 現在の値をUndo履歴に保存
        try:
            _, _, current_value = self._resolve_path(state_path)
            self._undo_stacks[state_path].append(copy.deepcopy(current_value))
        except (AttributeError, ValueError):
            return

        # Redo値を取得して適用
        self._during_ur_op = True  # 再帰防止フラグを設定
        try:
            redo_value = redo_stack.pop()
            self.update_state(state_path, redo_value)
        finally:
            self._during_ur_op = False

        # ステータス通知を送信
        self._emit_ur_status(state_path)

    def _emit_ur_status(self, state_path: str) -> None:
        """現在のUndo/Redo可否・スタックサイズを通知する。

        Args:
            state_path: ステータス通知対象の状態パス
        """
        undo_stack = self._undo_stacks.get(state_path, [])
        redo_stack = self._redo_stacks.get(state_path, [])
        self.publish(
            f"{DefaultUndoTopic.STATUS_CHANGED}.{state_path}",
            can_undo=len(undo_stack) > 1,
            can_redo=len(redo_stack) > 0,
            undo_count=max(len(undo_stack) - 1, 0),
            redo_count=len(redo_stack),
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
            model_fields = target_obj.__class__.model_fields

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
