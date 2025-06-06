# application_base.py - アプリケーションの基底クラスを定義

"""Tkinter アプリケーション向けの共通基底クラスを提供します。

このモジュールでは、Tk および ttk ベースのアプリケーション構築時に
利用する共通メソッドをまとめています。``TkApplication`` と
``ThemedApplication`` の 2 種類のウィンドウクラスを公開しており、
いずれも ``ApplicationCommon`` Mixin を継承して Pub/Sub 機能と
状態管理機能を自動的に組み込みます。
"""

from __future__ import annotations

import asyncio
import tkinter as tk
from typing import TYPE_CHECKING, Dict, Generic, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel
from ttkthemes import ThemedTk

from pubsubtk.core.default_topic_base import PubSubDefaultTopicBase
from pubsubtk.processor.processor_base import ProcessorBase
from pubsubtk.store.store import get_store
from pubsubtk.topic.topics import DefaultNavigateTopic, DefaultProcessorTopic
from pubsubtk.ui.base.container_base import ContainerMixin
from pubsubtk.ui.base.template_base import TemplateMixin

if TYPE_CHECKING:
    from pubsubtk.ui.types import (
        ComponentType,
        ContainerComponentType,
        TemplateComponentType,
    )

TState = TypeVar("TState", bound=BaseModel)
P = TypeVar("P", bound=ProcessorBase)


def _default_poll(loop: asyncio.AbstractEventLoop, root: tk.Tk, interval: int) -> None:
    """非同期イベントループを ``after`` で定期実行する補助関数。

    Args:
        loop: 実行対象の ``AbstractEventLoop`` インスタンス。
        root: ``after`` を呼び出す Tk ウィジェット（通常はアプリケーション本体）。
        interval: ポーリング間隔（ミリ秒）。
    """

    try:
        loop.call_soon(loop.stop)
        loop.run_forever()
    except Exception:
        pass
    root.after(interval, _default_poll, loop, root, interval)


class ApplicationCommon(PubSubDefaultTopicBase, Generic[TState]):
    """Tk/Ttk いずれのウィンドウクラスでも共通の機能を提供する Mixin."""

    def __init__(self, state_cls: Type[TState], *args, **kwargs):
        """状態クラスを受け取り、Pub/Sub 機能を初期化する。

        Args:
            state_cls: アプリケーション状態を表す ``BaseModel`` のサブクラス。
        """

        super().__init__(*args, **kwargs)
        self.state_cls = state_cls
        self.store = get_store(state_cls)
        self._processors: Dict[str, ProcessorBase] = {}

    def init_common(self, title: str, geometry: str) -> None:
        """ウィンドウタイトルやメインフレームを設定する共通初期化処理。

        Args:
            title: ウィンドウタイトル。
            geometry: ``WIDTHxHEIGHT`` 形式のウィンドウサイズ文字列。
        """

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
        """PubSub の購読設定を行う。

        ``PubSubBase.__init__`` から自動で呼び出されるメソッドで、
        ナビゲーションや Processor 管理に関するトピックを購読します。
        """

        self.subscribe(DefaultNavigateTopic.SWITCH_CONTAINER, self.switch_container)
        self.subscribe(DefaultNavigateTopic.SWITCH_SLOT, self.switch_slot)
        self.subscribe(DefaultNavigateTopic.OPEN_SUBWINDOW, self.open_subwindow)
        self.subscribe(DefaultNavigateTopic.CLOSE_SUBWINDOW, self.close_subwindow)
        self.subscribe(
            DefaultNavigateTopic.CLOSE_ALL_SUBWINDOWS, self.close_all_subwindows
        )
        self.subscribe(
            DefaultProcessorTopic.REGISTER_PROCESSOR, self.register_processor
        )
        self.subscribe(DefaultProcessorTopic.DELETE_PROCESSOR, self.delete_processor)

    def _create_component(
        self, cls: ComponentType, parent: tk.Widget, kwargs: dict = None
    ) -> tk.Widget:
        """コンポーネントを種類に応じて生成する共通メソッド。

        Args:
            cls: コンポーネントのクラス。
            parent: 親ウィジェット。
            kwargs: コンポーネント初期化用パラメータ辞書。

        Returns:
            生成したウィジェットインスタンス。
        """
        kwargs = kwargs or {}

        # ContainerMixinを継承しているかチェック
        is_container = issubclass(cls, ContainerMixin)

        if is_container:
            # Containerの場合はstoreを渡す
            return cls(parent=parent, store=self.store, **kwargs)
        else:
            # Presentationalの場合はstoreなし
            return cls(parent=parent, **kwargs)

    def register_processor(self, proc: Type[P], name: Optional[str] = None) -> str:
        """
        プロセッサを名前で登録し、登録キーを返します。

        Args:
            proc: ProcessorBaseを継承したクラス
            name: 任意のプロセッサ名。未指定時はクラス名を使用し、重複する場合は接尾辞を追加します。
        Returns:
            登録に使用したプロセッサ名。
        Raises:
            KeyError: 既に同名のプロセッサが登録済みの場合。
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
        """登録済みプロセッサを削除し ``teardown`` を実行する。"""
        if name not in self._processors:
            raise KeyError(f"Processor '{name}' not found.")
        self._processors[name].teardown()
        del self._processors[name]

    def set_template(self, template_cls: TemplateComponentType) -> None:
        """アプリケーションにテンプレートを設定する。

        Args:
            template_cls: 適用する ``TemplateComponent`` のクラス。
        """
        if self.active:
            self.active.destroy()
        self.active = template_cls(parent=self.main_frame, store=self.store)
        self.active.pack(fill=tk.BOTH, expand=True)

    def switch_container(
        self,
        cls: ContainerComponentType,
        kwargs: dict = None,
    ) -> None:
        """メインフレーム内のコンテナを切り替える。

        テンプレートが設定されている場合は ``switch_slot`` を使用して
        デフォルトスロットのコンテンツを置き換えます。

        Args:
            cls: 切り替え先のコンテナクラス。
            kwargs: コンテナ初期化用のキーワード引数辞書。
        """
        # テンプレートが設定されている場合
        if self.active and isinstance(self.active, TemplateMixin):
            # デフォルトスロット（"main" または "content"）を探す
            slots = self.active.get_slots()
            if "main" in slots:
                self.active.switch_slot_content("main", cls, kwargs)
            elif "content" in slots:
                self.active.switch_slot_content("content", cls, kwargs)
            else:
                # デフォルトスロットがない場合は最初のスロットを使用
                if slots:
                    first_slot = list(slots.keys())[0]
                    self.active.switch_slot_content(first_slot, cls, kwargs)
                else:
                    raise RuntimeError("Template has no slots defined")
        else:
            # 通常のコンテナ切り替え
            if self.active:
                self.active.destroy()
            kwargs = kwargs or {}
            self.active = self._create_component(cls, self.main_frame, kwargs)
            self.active.pack(fill=tk.BOTH, expand=True)

    def switch_slot(
        self,
        slot_name: str,
        cls: ComponentType,
        kwargs: dict = None,
    ) -> None:
        """テンプレートの特定スロットのコンテンツを切り替える。

        Args:
            slot_name: 変更対象のスロット名。
            cls: 新しく配置するコンポーネントクラス。
            kwargs: コンポーネント初期化用のキーワード引数辞書。
        """
        if not self.active or not isinstance(self.active, TemplateMixin):
            raise RuntimeError("No template is set. Use set_template() first.")

        self.active.switch_slot_content(slot_name, cls, kwargs)

    def open_subwindow(
        self,
        cls: ComponentType,
        win_id: Optional[str] = None,
        kwargs: dict = None,
    ) -> str:
        """サブウィンドウを開き、生成したウィンドウ ID を返す。

        Args:
            cls: 表示するコンポーネントクラス。
            win_id: 任意のウィンドウ ID。指定しない場合は自動生成される。
            kwargs: コンポーネント初期化用のキーワード引数辞書。

        Returns:
            実際に使用されたウィンドウ ID。
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

        # 共通メソッドを使用
        comp = self._create_component(cls, toplevel, kwargs)
        comp.pack(fill=tk.BOTH, expand=True)

        def on_close():
            self.close_subwindow(unique_id)

        toplevel.protocol("WM_DELETE_WINDOW", on_close)

        self._subwindows[unique_id] = (toplevel, comp)
        return unique_id

    def close_subwindow(self, win_id: str) -> None:
        """指定 ID のサブウィンドウを閉じる。"""

        if win_id not in self._subwindows:
            return
        top, comp = self._subwindows.pop(win_id)
        try:
            comp.destroy()
        except Exception:
            pass
        top.destroy()

    def close_all_subwindows(self) -> None:
        """開いているすべてのサブウィンドウを閉じる。"""

        for wid in list(self._subwindows):
            self.close_subwindow(wid)

    def run(
        self,
        use_async: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        poll_interval: int = 50,
    ) -> None:
        """アプリケーションのメインループを開始する。

        Args:
            use_async: ``asyncio`` を併用するかどうか。
            loop: 使用するイベントループ。``None`` の場合は ``get_event_loop`` を使用。
            poll_interval: ``_default_poll`` を呼び出す間隔（ミリ秒）。
        """

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
        """終了時のクリーンアップ処理を行う。

        すべてのサブウィンドウを閉じて ``destroy`` を呼び出す。
        """

        self.close_all_subwindows()
        self.destroy()


class TkApplication(ApplicationCommon[TState], tk.Tk, Generic[TState]):
    def __init__(
        self,
        state_cls: Type[TState],
        title: str = "Tk App",
        geometry: str = "800x600",
        *args,
        **kwargs,
    ):
        """Tk ベースのアプリケーションを初期化する。

        Args:
            state_cls: アプリケーション状態モデルの型。
            title: ウィンドウタイトル。
            geometry: ``WIDTHxHEIGHT`` 形式のウィンドウサイズ。
        """

        # **first** initialize the actual Tk
        tk.Tk.__init__(self, *args, **kwargs)
        # **then** initialize the PubSub mixin
        ApplicationCommon.__init__(self, state_cls)
        # now do your common window setup
        self.init_common(title, geometry)


class ThemedApplication(ApplicationCommon[TState], ThemedTk, Generic[TState]):
    def __init__(
        self,
        state_cls: Type[TState],
        theme: str = "arc",
        title: str = "Themed App",
        geometry: str = "800x600",
        *args,
        **kwargs,
    ):
        """テーマ対応アプリケーションを初期化する。

        Args:
            state_cls: アプリケーション状態モデルの型。
            theme: 適用する ttk テーマ名。
            title: ウィンドウタイトル。
            geometry: ``WIDTHxHEIGHT`` 形式のウィンドウサイズ。
        """

        # initialize the themed‐Tk
        ThemedTk.__init__(self, theme=theme, *args, **kwargs)
        # mixin init
        ApplicationCommon.__init__(self, state_cls)
        # then common setup
        self.init_common(title, geometry)
