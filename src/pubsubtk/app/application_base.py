import asyncio
import tkinter as tk
from typing import Dict, Generic, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel
from ttkthemes import ThemedTk

from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.processor.processor_base import ProcessorBase
from pubsubtk.store.store import get_store
from pubsubtk.topic.topics import DefaultNavigateTopic, DefaultProcessorTopic
from pubsubtk.ui.base.container_base import ContainerComponentType

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
        comp = cls(parent=toplevel, store=self.store, **kwargs)
        comp.pack(fill=tk.BOTH, expand=True)
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
        ThemedTk.__init__(self, *args, theme=theme, **kwargs)
        # mixin init
        ApplicationCommon.__init__(self, state_cls)
        # then common setup
        self.init_common(title, geometry)
