# PubSubTk Library - AI Reference Guide

## Overview
PubSubTk is a Python library that provides a clean, type-safe way to build Tkinter/ttk GUI applications using the Publish-Subscribe pattern with Pydantic state management. It simplifies GUI development by separating concerns and enabling reactive UI updates.

## Core Concepts

### 1. State Management with Store
- **Type-safe state** using Pydantic models
- **Centralized state** with automatic change notifications
- **Path-based updates** with IDE support via proxy objects

### 2. PubSub Communication
- **Decoupled components** communicating via topics
- **Built-in default topics** for common operations
- **Custom topics** using AutoNamedTopic enum

### 3. Component Architecture
- **Container Components**: Stateful components with Store access
- **Presentational Components**: Pure display components
- **Processors**: Business logic handlers

## Full Source Code

### Core PubSub System

#### `src/pubsubtk/core/pubsub_base.py`
```python
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

from pubsub import pub

# PubSub専用のロガーを作成
_pubsub_logger = logging.getLogger("pubsubtk.pubsub")


class PubSubBase(ABC):
    """
    PubSubパターンの基底クラス。

    - setup_subscriptions()で購読設定を行う抽象メソッドを提供
    - subscribe()/send_message()/unsubscribe()/unsubscribe_all()で購読管理
    - teardown()で全購読解除
    - 継承先で購読設定を簡潔に記述可能
    - DEBUGレベルでPubSub操作をログ出力
    """

    def __init__(self, *args, **kwargs):
        self._subscriptions: List[Dict[str, Any]] = []
        self.setup_subscriptions()

    def subscribe(self, topic: str, handler: Callable, **kwargs) -> None:
        pub.subscribe(handler, topic, **kwargs)
        self._subscriptions.append({"topic": topic, "handler": handler})
        
        # DEBUGログ：購読登録
        _pubsub_logger.debug(
            f"SUBSCRIBE: {self.__class__.__name__} -> topic='{topic}', handler={handler.__name__}"
        )

    def publish(self, topic: str, **kwargs) -> None:
        # DEBUGログ：パブリッシュ（引数も表示）
        args_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        _pubsub_logger.debug(
            f"PUBLISH: {self.__class__.__name__} -> topic='{topic}'" + 
            (f" with args: {args_str}" if args_str else "")
        )
        
        pub.sendMessage(topic, **kwargs)

    def unsubscribe(self, topic: str, handler: Callable) -> None:
        pub.unsubscribe(handler, topic)
        self._subscriptions = [
            s
            for s in self._subscriptions
            if not (s["topic"] == topic and s["handler"] == handler)
        ]
        
        # DEBUGログ：購読解除
        _pubsub_logger.debug(
            f"UNSUBSCRIBE: {self.__class__.__name__} -> topic='{topic}', handler={handler.__name__}"
        )

    def unsubscribe_all(self) -> None:
        # DEBUGログ：全購読解除
        if self._subscriptions:
            _pubsub_logger.debug(
                f"UNSUBSCRIBE_ALL: {self.__class__.__name__} -> {len(self._subscriptions)} subscriptions"
            )
        
        for s in list(self._subscriptions):
            pub.unsubscribe(s["handler"], s["topic"])
        self._subscriptions.clear()

    @abstractmethod
    def setup_subscriptions(self) -> None:
        """
        継承先で購読設定を行うためのメソッド。

        例:
            class MyPS(PubSubBase):
                def setup_subscriptions(self):
                    self.subscribe(TopicEnum.STATE_CHANGED, self.on_change)
        """
        pass

    def teardown(self) -> None:
        """
        全ての購読を解除する。
        """
        self.unsubscribe_all()


# デバッグログを有効化するユーティリティ関数
def enable_pubsub_debug_logging(level: int = logging.DEBUG) -> None:
    """
    PubSubのデバッグログを有効化する。
    
    Args:
        level: ログレベル（デフォルト: DEBUG）
    
    使用例:
        from pubsubtk.core.pubsub_base import enable_pubsub_debug_logging
        enable_pubsub_debug_logging()
    """
    _pubsub_logger.setLevel(level)
    
    # ハンドラーが未設定の場合はコンソールハンドラーを追加
    if not _pubsub_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        _pubsub_logger.addHandler(handler)
    
    _pubsub_logger.debug("PubSub debug logging enabled")


def disable_pubsub_debug_logging() -> None:
    """
    PubSubのデバッグログを無効化する。
    """
    _pubsub_logger.setLevel(logging.WARNING)
    _pubsub_logger.debug("PubSub debug logging disabled")
```

#### `src/pubsubtk/core/default_topic_base.py`
```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional, Type

from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.topic.topics import (
    DefaultNavigateTopic,
    DefaultProcessorTopic,
    DefaultUpdateTopic,
)

if TYPE_CHECKING:
    # 型チェック時（mypy や IDE 補完時）のみ読み込む
    from pubsubtk.processor.processor_base import ProcessorBase
    from pubsubtk.ui.base.container_base import ContainerComponentType


class PubSubDefaultTopicBase(PubSubBase):
    """
    Built-in convenience methods for common PubSub operations.
    
    **IMPORTANT**: Container and Processor components should use these built-in methods
    instead of manually publishing to DefaultTopics. These methods are designed for
    ease of use and provide better IDE support.
    """
    
    def pub_switch_container(
        self,
        cls: ContainerComponentType,
        kwargs: dict = None,
    ) -> None:
        """コンテナを切り替えるPubSubメッセージを送信する。

        Args:
            cls (ContainerComponentType): 切り替え先のコンテナコンポーネントクラス
            kwargs: コンテナに渡すキーワード引数用辞書

        Note:
            コンテナは、TkApplicationまたはTtkApplicationのコンストラクタで指定された
            親ウィジェットの子として配置されます。
        """
        self.publish(DefaultNavigateTopic.SWITCH_CONTAINER, cls=cls, kwargs=kwargs)

    def pub_open_subwindow(
        self,
        cls: ContainerComponentType,
        win_id: Optional[str] = None,
        kwargs: dict = None,
    ) -> None:
        """サブウィンドウを開くPubSubメッセージを送信する。

        Args:
            cls (ContainerComponentType): サブウィンドウに表示するコンテナコンポーネントクラス
            win_id (Optional[str], optional): サブウィンドウのID。
                指定しない場合は自動生成される。
                同じIDを指定すると、既存のウィンドウが再利用される。
            kwargs: コンテナに渡すキーワード引数用辞書

        Note:
            サブウィンドウは、Toplevel ウィジェットとして作成されます。
        """
        self.publish(
            DefaultNavigateTopic.OPEN_SUBWINDOW, cls=cls, win_id=win_id, kwargs=kwargs
        )

    def pub_close_subwindow(self, win_id: str) -> None:
        """サブウィンドウを閉じるPubSubメッセージを送信する。

        Args:
            win_id (str): 閉じるサブウィンドウのID
        """
        self.publish(DefaultNavigateTopic.CLOSE_SUBWINDOW, win_id=win_id)

    def pub_close_all_subwindows(self) -> None:
        """すべてのサブウィンドウを閉じるPubSubメッセージを送信する。"""
        self.publish(DefaultNavigateTopic.CLOSE_ALL_SUBWINDOWS)

    def pub_update_state(self, state_path: str, new_value: Any) -> None:
        """
        Storeの状態を更新するPubSubメッセージを送信する。

        Args:
            state_path (str): 更新する状態のパス（例: "user.name", "items[2].value"）
            new_value (Any): 新しい値

        Note:
            **RECOMMENDED**: Use store.state proxy for type-safe paths with IDE support:
            `self.pub_update_state(str(self.store.state.user.name), "新しい名前")`
            The state proxy provides autocomplete and "Go to Definition" functionality.
        """
        self.publish(
            DefaultUpdateTopic.UPDATE_STATE,
            state_path=str(state_path),
            new_value=new_value,
        )

    def pub_add_to_list(self, state_path: str, item: Any) -> None:
        """
        Storeの状態（リスト）に要素を追加するPubSubメッセージを送信する。

        Args:
            state_path (str): 要素を追加するリストの状態パス（例: "items", "user.tasks"）
            item (Any): 追加する要素

        Note:
            **RECOMMENDED**: Use store.state proxy for type-safe paths with IDE support:
            `self.pub_add_to_list(str(self.store.state.items), new_item)`
            The state proxy provides autocomplete and "Go to Definition" functionality.
        """
        self.publish(
            DefaultUpdateTopic.ADD_TO_LIST, state_path=str(state_path), item=item
        )

    def pub_registor_processor(
        self,
        proc: Type[ProcessorBase],
        name: Optional[str] = None,
    ) -> None:
        """Processorを登録するPubSubメッセージを送信する。

        Args:
            proc (Type[ProcessorBase]): 登録するProcessorクラス
            name (Optional[str], optional): Processorの名前。
                省略した場合はクラス名が使用される。Defaults to None.

        Note:
            登録されたProcessorは、アプリケーションのライフサイクルを通じて有効です。
        """
        self.publish(DefaultProcessorTopic.REGISTOR_PROCESSOR, proc=proc, name=name)

    def pub_delete_processor(self, name: str) -> None:
        """指定した名前のProcessorを削除するPubSubメッセージを送信する。

        Args:
            name (str): 削除するProcessorの名前
        """
        self.publish(DefaultProcessorTopic.DELETE_PROCESSOR, name=name)

    def sub_state_changed(
        self, state_path: str, handler: Callable[[Any, Any], None]
    ) -> None:
        """
        状態が変更されたときの通知を購読する。

        ハンドラー関数には、old_valueとnew_valueが渡されます。

        Args:
            state_path (str): 監視する状態のパス（例: "user.name", "items[2].value"）
            handler (Callable[[Any, Any], None]): 変更時に呼び出される関数。
                old_valueとnew_valueの2引数を取る
        
        Note:
            **RECOMMENDED**: Use store.state proxy for consistent path specification:
            `self.sub_state_changed(str(self.store.state.user.name), self.on_name_changed)`
        """
        self.subscribe(f"{DefaultUpdateTopic.STATE_CHANGED}.{str(state_path)}", handler)

    def sub_state_added(
        self, state_path: str, handler: Callable[[Any, int], None]
    ) -> None:
        """
        リストに要素が追加されたときの通知を購読する。

        ハンドラー関数には、itemとindexが渡されます。

        Args:
            state_path (str): 監視するリスト状態のパス（例: "items", "user.tasks"）
            handler (Callable[[Any, int], None]): 要素追加時に呼び出される関数。
                追加されたアイテムとそのインデックスを引数に取る
        
        Note:
            **RECOMMENDED**: Use store.state proxy for consistent path specification:
            `self.sub_state_added(str(self.store.state.items), self.on_item_added)`
        """
        self.subscribe(f"{DefaultUpdateTopic.STATE_ADDED}.{str(state_path)}", handler)
```

### Topics System

#### `src/pubsubtk/topic/topics.py`
```python
from enum import StrEnum, auto


class AutoNamedTopic(StrEnum):
    """
    Enumメンバー名を自動で小文字化し、クラス名のプレフィックス付き文字列を値とする列挙型。

    - メンバー値は "ClassName.member" 形式の文字列
    - str()や比較でそのまま利用可能
    """

    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    def __new__(cls, value):
        # ここでクラス名プレフィックスを追加
        full = f"{cls.__name__}.{value}"
        obj = str.__new__(cls, full)
        obj._value_ = full
        return obj

    def __str__(self):
        return self.value


class DefaultNavigateTopic(AutoNamedTopic):
    """
    標準的な画面遷移・ウィンドウ操作用のPubSubトピック列挙型。
    """

    SWITCH_CONTAINER = auto()
    OPEN_SUBWINDOW = auto()
    CLOSE_SUBWINDOW = auto()
    CLOSE_ALL_SUBWINDOWS = auto()


class DefaultUpdateTopic(AutoNamedTopic):
    """
    標準的な状態更新通知用のPubSubトピック列挙型。
    """

    UPDATE_STATE = auto()
    ADD_TO_LIST = auto()
    STATE_CHANGED = auto()
    STATE_ADDED = auto()


class DefaultProcessorTopic(AutoNamedTopic):
    """
    標準的なプロセッサ管理のPubSubトピック列挙型。
    """

    REGISTOR_PROCESSOR = auto()
    DELETE_PROCESSOR = auto()
```

### State Management

#### `src/pubsubtk/store/store.py`
```python
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
        return f"{self._path}"

    __str__ = __repr__


class Store(PubSubBase, Generic[TState]):
    """
    型安全な状態管理を提供するジェネリックなStoreクラス。

    - Pydanticモデルを状態として保持し、状態操作を提供
    - get_current_state()で状態のディープコピーを取得
    - update_state()/add_to_list()で状態を更新し、PubSubで通知
    - create_partial_state_updater()で部分更新用関数を生成
    
    **KEY FEATURE**: store.state proxy provides IDE autocomplete and type checking
    for state paths. Always prefer `str(store.state.field)` over string literals.
    
    Usage: `str(self.store.state.user.name)` -> "user.name" with IDE support
    """

    def __init__(self, initial_state_class: Type[TState]):
        """
        Storeを初期化する。

        Args:
            initial_state_class: Pydanticモデルの型
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
        
        **USAGE**: str(self.store.state.user.name) -> "user.name" with IDE support
        The proxy provides IDE autocomplete and "Go to Definition" functionality.
        """
        return cast(TState, StateProxy(self))

    def get_current_state(self) -> TState:
        """
        現在の状態のディープコピーを返す。
        """
        return self._state.model_copy(deep=True)

    def update_state(self, state_path: str, new_value: Any) -> None:
        """
        指定パスの属性を新しい値で更新し、PubSubで変更通知を送信する。

        Args:
            state_path: 属性パス（例: "foo.bar"）
            new_value: 新しい値
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
        """
        指定パスのリスト属性に要素を追加し、PubSubで追加通知を送信する。

        Args:
            state_path: 属性パス
            item: 追加する要素
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
_store: Optional[Store[Any]] = None


def get_store(state_cls: Type[TState]) -> Store[TState]:
    """
    Store を取得します。未生成の場合は state_cls で新規に作成し、
    それ以外は既存のインスタンスを返します。

    同じモジュール内で異なる state_cls を渡すと RuntimeError を投げます。
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
```

### Application Classes

#### `src/pubsubtk/app/application_base.py`
```python
import asyncio
import tkinter as tk
from typing import Dict, Generic, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel
from ttkthemes import ThemedTk

from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.processor.processor_base import ProcessorBase
from pubsubtk.store.store import get_store
from pubsubtk.topic.topics import DefaultNavigateTopic, DefaultProcessorTopic
from pubsubtk.ui.base.container_base import ContainerComponentType, ContainerMixin

TState = TypeVar("TState", bound=BaseModel)
P = TypeVar("P", bound=ProcessorBase)


def _default_poll(loop: asyncio.AbstractEventLoop, root: tk.Tk, interval: int) -> None:
    try:
        loop.call_soon(loop.stop)
        loop.run_forever()
    except Exception:
        pass
    root.after(interval, _default_poll, loop, root, interval)


class ApplicationCommon(PubSubBase, Generic[TState]):
    """Tk/Ttk いずれのウィンドウクラスでも共通の機能を提供する Mixin"""

    def __init__(self, state_cls: Type[TState], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_cls = state_cls
        self.store = get_store(state_cls)
        self._processors: Dict[str, ProcessorBase] = {}

    def init_common(self, title: str, geometry: str) -> None:
        # ウィンドウ基本設定
        self.title(title)
        self.geometry(geometry)

        # コンテナ & アクティブウィジェット
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.active: Optional[tk.Widget] = None

        # サブウィンドウ管理用辞書
        self._subwindows: Dict[str, Tuple[tk.Toplevel, tk.Widget]] = {}

    def setup_subscriptions(self) -> None:
        # PubSubBase.__init__ 内から自動呼び出しされる
        self.subscribe(DefaultNavigateTopic.SWITCH_CONTAINER, self.switch_container)
        self.subscribe(DefaultNavigateTopic.OPEN_SUBWINDOW, self.open_subwindow)
        self.subscribe(DefaultNavigateTopic.CLOSE_SUBWINDOW, self.close_subwindow)
        self.subscribe(
            DefaultNavigateTopic.CLOSE_ALL_SUBWINDOWS, self.close_all_subwindows
        )
        self.subscribe(
            DefaultProcessorTopic.REGISTOR_PROCESSOR, self.register_processor
        )
        self.subscribe(DefaultProcessorTopic.DELETE_PROCESSOR, self.delete_processor)

    def register_processor(self, proc: Type[P], name: Optional[str] = None) -> str:
        """
        プロセッサを名前で登録し、登録キーを返します。

        Args:
            proc: ProcessorBaseを継承したクラス
            name: 任意のプロセッサ名。未指定時はクラス名を使用し、重複する場合は接尾辞を追加します。
        Returns:
            登録に使用したプロセッサ名
        Raises:
            KeyError: 既に同名のプロセッサが登録済みの場合（自動生成でも重複が解消されない場合）
        """
        # ベース名決定
        base_key = name or proc.__name__
        key = base_key
        suffix = 1
        # 重複を回避
        while key in self._processors:
            key = f"{base_key}_{suffix}"
            suffix += 1

        # インスタンス化して登録
        self._processors[key] = proc(store=self.store)
        return key

    def delete_processor(self, name: str) -> None:
        """
        登録済みプロセッサを削除し、teardown()を呼び出します。
        """
        if name not in self._processors:
            raise KeyError(f"Processor '{name}' not found.")
        self._processors[name].teardown()
        del self._processors[name]

    def switch_container(
        self,
        cls: ContainerComponentType,
        kwargs: dict = None,
    ) -> None:
        """
        メインフレーム内のコンテナを切り替えます。

        Args:
            cls: コンテナクラス
            kwargs: コンテナ初期化用パラメータ辞書
        """
        if self.active:
            self.active.destroy()
        kwargs = kwargs or {}
        self.active = cls(parent=self.main_frame, store=self.store, **kwargs)
        self.active.pack(fill=tk.BOTH, expand=True)

    def open_subwindow(
        self,
        cls: ContainerComponentType,
        win_id: Optional[str] = None,
        kwargs: dict = None,
    ) -> str:
        """
        サブウィンドウを開き、ウィンドウIDを返します。

        Args:
            win_id: 任意のウィンドウキー。未指定または重複時は自動生成します。
            cls: ウィジェットクラス
            kwargs: コンテナ初期化用パラメータ辞書
        Returns:
            使用したウィンドウID
        """
        # 既存IDであれば前面に
        if win_id and win_id in self._subwindows:
            self._subwindows[win_id][0].lift()
            return win_id

        # キー生成
        base_id = win_id or cls.__name__
        unique_id = base_id
        suffix = 1
        while unique_id in self._subwindows:
            unique_id = f"{base_id}_{suffix}"
            suffix += 1

        # ウィンドウ生成
        toplevel = tk.Toplevel(self)
        kwargs = kwargs or {}
        kwargs["win_id"] = unique_id

        # PresentationalComponentならstore不要
        is_container = issubclass(cls, ContainerMixin)
        if is_container:
            comp = cls(parent=toplevel, store=self.store, **kwargs)
        else:
            comp = cls(parent=toplevel, **kwargs)

        comp.pack(fill=tk.BOTH, expand=True)

        def on_close():
            self.close_subwindow(unique_id)

        toplevel.protocol("WM_DELETE_WINDOW", on_close)

        self._subwindows[unique_id] = (toplevel, comp)
        return unique_id

    def close_subwindow(self, win_id: str) -> None:
        if win_id not in self._subwindows:
            return
        top, comp = self._subwindows.pop(win_id)
        try:
            comp.destroy()
        except Exception:
            pass
        top.destroy()

    def close_all_subwindows(self) -> None:
        for wid in list(self._subwindows):
            self.close_subwindow(wid)

    def run(
        self,
        use_async: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        poll_interval: int = 50,
    ) -> None:
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        if not use_async:
            self.mainloop()
        else:
            loop = loop or asyncio.get_event_loop()
            self.after(poll_interval, _default_poll, loop, self, poll_interval)
            self.mainloop()
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass

    def on_closing(self) -> None:
        self.close_all_subwindows()
        self.destroy()


class TkApplication(ApplicationCommon, tk.Tk):
    def __init__(
        self,
        state_cls: Type[TState],
        title: str = "Tk App",
        geometry: str = "800x600",
        *args,
        **kwargs,
    ):
        # **first** initialize the actual Tk
        tk.Tk.__init__(self, *args, **kwargs)
        # **then** initialize the PubSub mixin
        ApplicationCommon.__init__(self, state_cls)
        # now do your common window setup
        self.init_common(title, geometry)


class ThemedApplication(ApplicationCommon, ThemedTk):
    def __init__(
        self,
        state_cls: Type[TState],
        theme: str = "arc",
        title: str = "Themed App",
        geometry: str = "800x600",
        *args,
        **kwargs,
    ):
        # initialize the themed‐Tk
        ThemedTk.__init__(self, theme=theme, *args, **kwargs)
        # mixin init
        ApplicationCommon.__init__(self, state_cls)
        # then common setup
        self.init_common(title, geometry)
```

### UI Components

#### `src/pubsubtk/ui/base/container_base.py`
```python
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from typing import Any, Generic, Type, TypeVar

from pydantic import BaseModel

from pubsubtk.core.default_topic_base import PubSubDefaultTopicBase
from pubsubtk.store.store import Store

TState = TypeVar("TState", bound=BaseModel)


class ContainerMixin(PubSubDefaultTopicBase, ABC, Generic[TState]):
    """
    PubSub連携用のコンテナコンポーネントMixin。

    - Storeインスタンスを取得し、購読設定・状態反映を自動実行
    - setup_subscriptions()/refresh_from_state()をサブクラスで実装
    - destroy時に購読解除(teardown)も自動
    
    **IMPORTANT**: Use built-in pub_* methods for state updates instead of 
    manually publishing to topics. This provides better IDE support and consistency.
    """

    def __init__(self, store: Store[TState], *args, **kwargs: Any):
        """
        Args:
            state_cls: Pydanticモデルの型（例: AppState）
        """
        self.args = args
        self.kwargs = kwargs

        # 型引数付きの Store[TState] を取得
        self.store: Store[TState] = store

        super().__init__(*args, **kwargs)

        self.setup_ui()
        self.refresh_from_state()

    @abstractmethod
    def setup_ui(self) -> None:
        """
        ウィジェット構築とレイアウトを行うメソッド。
        サブクラスで実装する。
        """
        ...

    @abstractmethod
    def refresh_from_state(self) -> None:
        """
        購読通知または初期化時にUIを状態で更新するメソッド。
        サブクラスで実装する。
        """
        ...

    def destroy(self) -> None:
        """
        ウィジェット破棄時に購読を解除してから破棄処理を行う。
        """
        self.teardown()
        super().destroy()


class ContainerComponentTk(ContainerMixin[TState], tk.Frame, Generic[TState]):
    """
    標準tk.FrameベースのPubSub連携コンテナ。
    """

    def __init__(self, parent: tk.Widget, store: Store[TState], *args, **kwargs: Any):
        tk.Frame.__init__(self, master=parent)
        ContainerMixin.__init__(self, store=store, *args, **kwargs)


class ContainerComponentTtk(ContainerMixin[TState], ttk.Frame, Generic[TState]):
    """
    テーマ対応ttk.FrameベースのPubSub連携コンテナ。
    """

    def __init__(self, parent: tk.Widget, store: Store[TState], *args, **kwargs: Any):
        ttk.Frame.__init__(self, master=parent)
        ContainerMixin.__init__(self, store=store, *args, **kwargs)


ContainerComponentType = Type[ContainerComponentTk] | Type[ContainerComponentTtk]
```

#### `src/pubsubtk/ui/base/presentaional_base.py`
```python
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from typing import Any, Callable, Dict


class PresentationalMixin(ABC):
    """
    表示専用コンポーネント用のMixin。

    - 外部データでUIを更新するupdate_data()を抽象メソッドとして提供
    - 任意のイベントハンドラ登録・発火機能を持つ
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        self._handlers: Dict[str, Callable[..., Any]] = {}
        self.setup_ui()

    @abstractmethod
    def setup_ui(self) -> None:
        """
        ウィジェット構築とレイアウトを行うメソッド。
        サブクラスで実装する。
        """
        pass

    @abstractmethod
    def update_data(self, *args: Any, **kwargs: Any) -> None:
        """
        外部データでUIを更新するためのメソッド。
        サブクラスで実装する。
        """
        ...

    def register_handler(self, event_name: str, handler: Callable[..., Any]) -> None:
        self._handlers[event_name] = handler

    def trigger_event(self, event_name: str, **kwargs: Any) -> None:
        if handler := self._handlers.get(event_name):
            handler(**kwargs)


# tk.Frame ベース の抽象クラス
class PresentationalComponentTk(PresentationalMixin, tk.Frame):
    """
    標準tk.Frameベースの表示専用コンポーネント。
    """

    def __init__(self, parent: tk.Widget, *args, **kwargs):
        tk.Frame.__init__(self, master=parent)
        PresentationalMixin.__init__(self, *args, **kwargs)


# ttk.Frame ベース の抽象クラス
class PresentationalComponentTtk(PresentationalMixin, ttk.Frame):
    """
    テーマ対応ttk.Frameベースの表示専用コンポーネント。
    """

    def __init__(self, parent: tk.Widget, *args, **kwargs):
        ttk.Frame.__init__(self, master=parent)
        PresentationalMixin.__init__(self, *args, **kwargs)
```

### Processor System

#### `src/pubsubtk/processor/processor_base.py`
```python
from typing import Generic, TypeVar

from pydantic import BaseModel

from pubsubtk.core.default_topic_base import PubSubDefaultTopicBase
from pubsubtk.store.store import Store

TState = TypeVar("TState", bound=BaseModel)


class ProcessorBase(PubSubDefaultTopicBase, Generic[TState]):
    """
    Business logic handlers with Store access and PubSub integration.
    
    **IMPORTANT**: Use built-in pub_* and sub_* methods for state operations
    instead of manually working with topics. This ensures consistency and
    provides better IDE support.
    """
    
    def __init__(self, store: Store[TState], *args, **kwargs):
        # 型引数付きの Store[TState] を取得
        self.store: Store[TState] = store

        super().__init__(*args, **kwargs)
```

### Built-in Method Usage (RECOMMENDED)

```python
# ✅ RECOMMENDED: Use built-in convenience methods
class MyContainer(ContainerComponentTk[AppState]):
    def some_action(self):
        # Use built-in methods - they're designed for ease of use
        self.pub_update_state(self.store.state.count, 42)
        self.pub_switch_container(OtherContainer)
        self.pub_open_subwindow(DialogContainer)

# ❌ NOT RECOMMENDED: Manual topic publishing
class MyContainer(ContainerComponentTk[AppState]):
    def some_action(self):
        # Don't do this - use the built-in methods instead
        self.publish(DefaultUpdateTopic.UPDATE_STATE, state_path="count", new_value=42)
```

### State Path Usage (RECOMMENDED)

```python
# ✅ RECOMMENDED: Use state proxy directly for most operations
self.pub_update_state(self.store.state.count, new_value)
self.pub_add_to_list(self.store.state.items, new_item)
self.sub_state_changed(self.store.state.user, self.on_user_changed)

# ✅ Wrap with str() when doing string operations to avoid proxy method conflicts
path = str(self.store.state.user.name) + "_backup"
base_path = str(self.store.state.items)
full_path = f"{base_path}.{index}"

# ❌ Don't do string operations directly on state proxy
# self.store.state.user.name.join(...)  # Error: state has no 'join' method
# self.store.state.items.split(...)     # Error: state has no 'split' method

# ✅ Also acceptable: Direct string paths
self.pub_update_state("count", new_value)
self.sub_state_changed("user.name", self.on_name_changed)

# The state proxy provides IDE autocomplete and "Go to Definition" support
```

## Key Design Patterns

### 1. State-First Architecture
Always define your application state as a Pydantic model first:

```python
from pydantic import BaseModel
from typing import List

class TodoItem(BaseModel):
    id: int
    text: str
    completed: bool = False

class AppState(BaseModel):
    todos: List[TodoItem] = []
    filter_mode: str = "all"
    next_id: int = 1
```

### 2. Application Setup Pattern
```python
import pubsubtk

class TodoApp(pubsubtk.TkApplication):
    def __init__(self):
        super().__init__(AppState, title="Todo App", geometry="600x400")
        # App automatically gets self.store with type-safe access
        
    def setup_custom_logic(self):
        # Register processors for business logic
        self.pub_registor_processor(TodoProcessor)
        
        # Switch to main container
        self.pub_switch_container(MainContainer)

if __name__ == "__main__":
    app = TodoApp()
    app.setup_custom_logic()
    app.run()
```

### 3. Container Component Pattern
```python
class MainContainer(pubsubtk.ContainerComponentTk[AppState]):
    def setup_ui(self):
        # Create UI elements
        self.entry = tk.Entry(self)
        self.add_btn = tk.Button(self, text="Add", command=self.add_todo)
        self.listbox = tk.Listbox(self)
        
        # Layout
        self.entry.pack(fill=tk.X, padx=5, pady=5)
        self.add_btn.pack(pady=5)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_subscriptions(self):
        # Listen to state changes
        self.sub_state_changed("todos", self.on_todos_changed)
    
    def refresh_from_state(self):
        # Update UI from current state
        state = self.store.get_current_state()
        self.listbox.delete(0, tk.END)
        for todo in state.todos:
            status = "✓" if todo.completed else "○"
            self.listbox.insert(tk.END, f"{status} {todo.text}")
    
    def add_todo(self):
        text = self.entry.get().strip()
        if text:
            # Use state proxy for type-safe path access
            self.pub_add_to_list(str(self.store.state.todos), TodoItem(
                id=self.store.get_current_state().next_id,
                text=text
            ))
            self.pub_update_state(str(self.store.state.next_id), 
                                self.store.get_current_state().next_id + 1)
            self.entry.delete(0, tk.END)
    
    def on_todos_changed(self, old_value, new_value):
        self.refresh_from_state()
```

### 4. Processor Pattern (Business Logic)
```python
class TodoProcessor(pubsubtk.ProcessorBase[AppState]):
    def setup_subscriptions(self):
        # Listen to custom topics
        self.subscribe("todo.complete", self.handle_complete_todo)
        self.subscribe("todo.delete", self.handle_delete_todo)
    
    def handle_complete_todo(self, todo_id: int):
        state = self.store.get_current_state()
        for i, todo in enumerate(state.todos):
            if todo.id == todo_id:
                updated_todo = todo.model_copy()
                updated_todo.completed = not updated_todo.completed
                self.pub_update_state(f"todos.{i}", updated_todo)
                break
    
    def handle_delete_todo(self, todo_id: int):
        state = self.store.get_current_state()
        new_todos = [todo for todo in state.todos if todo.id != todo_id]
        self.pub_update_state(str(self.store.state.todos), new_todos)
```

## Important Notes for AI Code Generation

### 1. Type Safety Rules
- **Always** use generic type parameters: `ContainerComponentTk[YourState]`
- **Always** pass the state class to application constructor: `TkApplication(YourState)`
- Use `str(self.store.state.field_name)` for state path in pub methods

### 2. State Update Patterns
```python
# ✅ Correct: Use pub methods for state updates
self.pub_update_state(str(self.store.state.count), new_value)
self.pub_add_to_list(str(self.store.state.items), new_item)

# ❌ Wrong: Don't call store methods directly in UI components
self.store.update_state("count", new_value)  # This breaks PubSub pattern
```

### 3. Component Lifecycle
- **Container components**: Get `store` parameter, implement `setup_ui()` and `refresh_from_state()`
- **Presentational components**: No store access, implement `setup_ui()` and `update_data()`
- **Processors**: Get `store` parameter, implement `setup_subscriptions()` for business logic

### 4. Common Import Pattern
```python
import tkinter as tk
import pubsubtk
from pydantic import BaseModel
from typing import List, Optional
```

### 5. Navigation Patterns
```python
# Switch main container
self.pub_switch_container(NewContainer, kwargs={"param": value})

# Open subwindow
self.pub_open_subwindow(DialogContainer, win_id="settings", kwargs={"param": value})

# Close specific subwindow
self.pub_close_subwindow("settings")

# Close all subwindows
self.pub_close_all_subwindows()
```

### 6. Debug Usage
```python
# Enable debug logging to see all PubSub activity
pubsubtk.enable_pubsub_debug_logging()

# Your app code here...

# Disable when not needed
pubsubtk.disable_pubsub_debug_logging()
```

### 7. State Proxy Usage
The state proxy enables IDE support and type safety:
```python
# ✅ Good: IDE can autocomplete and navigate to definition
path = str(self.store.state.user.name)
self.pub_update_state(path, "New Name")

# ✅ Also good: Direct string if you know the path
self.pub_update_state("user.name", "New Name")

# The proxy validates paths at runtime and provides __str__ representation
```

### 8. Error Handling
- State path errors raise `AttributeError` with descriptive messages
- Processor registration conflicts are handled automatically with suffix generation
- Missing processors raise `KeyError` with clear error messages

## Dependencies
- `pydantic`: State modeling and validation
- `pypubsub`: Internal PubSub implementation
- `ttkthemes`: Themed application support (optional)
- `tkinter`: GUI framework (built into Python)

### State Proxy for IDE Support
The state proxy system enables IDE features like autocomplete and "Go to Definition":

```python
# The proxy validates paths at runtime and provides string representation
path = str(self.store.state.user.email)  # -> "user.email"
self.pub_update_state(path, "new@email.com")

# IDE can navigate to AppState.user.email definition
# IDE provides autocomplete for available fields
```

This library enables clean separation of concerns, type-safe state management, and reactive UI updates in Tkinter applications through the PubSub pattern.