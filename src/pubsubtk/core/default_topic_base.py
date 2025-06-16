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
    - Undo/Redo 機能を提供
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

        # Undo履歴をキャプチャ
        self._capture_for_undo(str(state_path), old_value)

        # 型チェック後に設定
        self._validate_and_set_value(target_obj, attr_name, new_value)

        # 詳細な変更通知（old_value, new_valueを含む）
        self.publish(
            f"{DefaultUpdateTopic.STATE_CHANGED}.{state_path}",
            old_value=old_value,
            new_value=new_value,
        )
        # シンプルな更新通知
        self.publish(f"{DefaultUpdateTopic.STATE_UPDATED}.{state_path}")

    def add_to_list(self, state_path: str, item: Any) -> None:
        """リスト属性に要素を追加し、追加通知を送信する。"""
        target_obj, attr_name, current_list = self._resolve_path(str(state_path))
        if not isinstance(current_list, list):
            raise TypeError(f"Property at '{state_path}' is not a list")

        # Undo履歴をキャプチャ
        self._capture_for_undo(str(state_path), current_list)

        new_list = current_list.copy()
        new_list.append(item)
        self._validate_and_set_value(target_obj, attr_name, new_list)

        index = len(new_list) - 1
        self.publish(
            f"{DefaultUpdateTopic.STATE_ADDED}.{state_path}",
            item=item,
            index=index,
        )
        self.publish(f"{DefaultUpdateTopic.STATE_UPDATED}.{state_path}")

    def add_to_dict(self, state_path: str, key: str, value: Any) -> None:
        """辞書属性に要素を追加し、追加通知を送信する。"""
        target_obj, attr_name, current_dict = self._resolve_path(str(state_path))
        if not isinstance(current_dict, dict):
            raise TypeError(f"Property at '{state_path}' is not a dict")

        # Undo履歴をキャプチャ
        self._capture_for_undo(str(state_path), current_dict)

        new_dict = current_dict.copy()
        new_dict[key] = value
        self._validate_and_set_value(target_obj, attr_name, new_dict)

        self.publish(
            f"{DefaultUpdateTopic.DICT_ADDED}.{state_path}",
            key=key,
            value=value,
        )
        self.publish(f"{DefaultUpdateTopic.STATE_UPDATED}.{state_path}")

    # --- Undo/Redo 履歴管理機能 ---

    def _enable_undo_redo(self, state_path: str, max_history: int = 10) -> None:
        """Undo/Redoを有効化し、初回スナップショットとして現在値を記録。"""
        self._undo_enabled.add(state_path)
        self._max_histories[state_path] = max_history

        try:
            _, _, current_value = self._resolve_path(state_path)
            self._undo_stacks[state_path] = [copy.deepcopy(current_value)]
        except (AttributeError, ValueError):
            self._undo_stacks[state_path] = []
        self._redo_stacks[state_path].clear()

        # UI用ステータス通知
        self._emit_ur_status(state_path)

    def _disable_undo_redo(self, state_path: str) -> None:
        """Undo/Redoを無効化し、履歴を破棄。"""
        self._undo_enabled.discard(state_path)
        self._undo_stacks.pop(state_path, None)
        self._redo_stacks.pop(state_path, None)
        self._max_histories.pop(state_path, None)

        # UI用ステータス通知
        self._emit_ur_status(state_path)

    def _capture_for_undo(self, state_path: str, old_value: Any) -> None:
        """状態変更前に履歴を記録し、Redo履歴をクリア。"""
        if state_path not in self._undo_enabled or self._during_ur_op:
            return

        stack = self._undo_stacks[state_path]
        stack.append(copy.deepcopy(old_value))

        max_len = self._max_histories.get(state_path, 10)
        if len(stack) > max_len:
            stack.pop(0)

        self._redo_stacks[state_path].clear()

        # UI用ステータス通知
        self._emit_ur_status(state_path)

    def _undo(self, state_path: str) -> None:
        """1つ前の値に戻す。"""
        if state_path not in self._undo_enabled:
            return
        undo_stack = self._undo_stacks[state_path]
        if len(undo_stack) < 2:
            return

        try:
            _, _, current_value = self._resolve_path(state_path)
            self._redo_stacks[state_path].append(copy.deepcopy(current_value))
        except (AttributeError, ValueError):
            return

        self._during_ur_op = True
        try:
            undo_stack.pop()
            prev = undo_stack[-1]
            self.update_state(state_path, prev)
        finally:
            self._during_ur_op = False

        # UI用ステータス通知
        self._emit_ur_status(state_path)

    def _redo(self, state_path: str) -> None:
        """Redo履歴を適用する。"""
        if state_path not in self._undo_enabled:
            return
        redo_stack = self._redo_stacks[state_path]
        if not redo_stack:
            return

        try:
            _, _, current_value = self._resolve_path(state_path)
            self._undo_stacks[state_path].append(copy.deepcopy(current_value))
        except (AttributeError, ValueError):
            return

        self._during_ur_op = True
        try:
            next_val = redo_stack.pop()
            self.update_state(state_path, next_val)
        finally:
            self._during_ur_op = False

        # UI用ステータス通知
        self._emit_ur_status(state_path)

    def _emit_ur_status(self, state_path: str) -> None:
        """現在のUndo/Redo可否・スタックサイズを通知する."""
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
        """
        segments = path.split(".")
        if not segments:
            raise ValueError("Empty path")

        attr_name = segments[-1]
        current = self._state
        for segment in segments[:-1]:
            if not hasattr(current, segment):
                raise AttributeError(f"No such attribute: {segment} in path {path}")
            current = getattr(current, segment)

        if not hasattr(current, attr_name):
            raise AttributeError(f"No such attribute: {attr_name} in path {path}")
        old_value = getattr(current, attr_name)
        return current, attr_name, old_value

    def _validate_and_set_value(
        self, target_obj: Any, attr_name: str, new_value: Any
    ) -> None:
        """属性値を型検証してから設定する。"""
        if isinstance(target_obj, BaseModel):
            model_fields = target_obj.__class__.model_fields
            if attr_name in model_fields:
                field_info = model_fields[attr_name]
                if hasattr(new_value, "model_dump") and hasattr(
                    field_info.annotation, "model_validate"
                ):
                    validated = field_info.annotation.model_validate(new_value)
                    setattr(target_obj, attr_name, validated)
                    return
        setattr(target_obj, attr_name, new_value)


# グローバルStoreシングルトン
_store: Optional[Store[Any]] = None


def get_store(state_cls: Type[TState]) -> Store[TState]:
    """グローバルな Store インスタンスを取得します。"""
    global _store
    if _store is None:
        _store = Store(state_cls)
    else:
        existing = getattr(_store, "_state_class", None)
        if existing is not state_cls:
            raise RuntimeError(
                f"Store は既に {existing!r} で生成されています（state_cls={state_cls!r}）"
            )
    return cast(Store[TState], _store)
