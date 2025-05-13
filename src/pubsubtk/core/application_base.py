import asyncio
import tkinter as tk
from typing import Any, Dict, Optional, Tuple, Type, TypeVar

from pubsubtk.core.api import get_store
from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.core.topics import DefaultNavigateTopic

# 型変数: 任意の tk.Tk 派生ルート
R = TypeVar("R", bound=tk.Tk)


def _default_poll(loop: asyncio.AbstractEventLoop, root: tk.Tk, interval: int) -> None:
    """
    tkinter の after から呼び出し、asyncio イベントループをポーリング実行する。
    """
    try:
        loop.call_soon(loop.stop)
        loop.run_forever()
    except Exception:
        pass
    # interval ミリ秒後に再度ポーリング
    root.after(interval, _default_poll, loop, root, interval)


class ApplicationMixin(PubSubBase):
    """
    - Store の初期化
    - メインコンテナ切替え
    - サブウィンドウ管理
    - asyncio と tkinter ループの統合実行（オプション制御）
    - 終了時クリーンアップ
    """

    def __init__(
        self,
        *args: Any,
        title: str = "Tk App",
        geometry: str = "800x600",
        **kwargs: Any,
    ):
        # ① PubSub の初期化（setup_subscriptions を呼ぶ）
        PubSubBase.__init__(self)

        # ② Tk の初期化
        super(ApplicationMixin, self).__init__(*args, **kwargs)

        # ウィンドウ設定
        self.title(title)
        self.geometry(geometry)

        # グローバル状態管理
        self.store = get_store()

        # メインコンテナ
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.active: Optional[tk.Widget] = None

        # サブウィンドウ管理
        self._subwindows: Dict[str, Tuple[tk.Toplevel, tk.Widget]] = {}

    def setup_subscriptions(self) -> None:
        # DefaultNavigateTopic の各メンバーと、メソッドをマッピングして購読
        self.subscribe(DefaultNavigateTopic.SWITCH_CONTAINER, self.switch_container)
        self.subscribe(DefaultNavigateTopic.OPEN_SUBWINDOW, self.open_subwindow)
        self.subscribe(DefaultNavigateTopic.CLOSE_SUBWINDOW, self.close_subwindow)
        self.subscribe(
            DefaultNavigateTopic.CLOSE_ALL_SUBWINDOWS, self.close_all_subwindows
        )

    def switch_container(
        self,
        cls: Type[tk.Widget],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """メインフレーム内のコンテナを差し替え"""
        if self.active:
            self.active.destroy()
        self.active = cls(self.main_frame, *args, **kwargs)
        self.active.pack(fill=tk.BOTH, expand=True)

    def open_subwindow(
        self,
        win_id: str,
        cls: Type[tk.Widget],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """ID 指定でサブウィンドウを開き、同じ ID が既存ならフォーカス"""
        if win_id in self._subwindows:
            toplevel, _ = self._subwindows[win_id]
            toplevel.lift()
            return

        toplevel = tk.Toplevel(self)
        component = cls(toplevel, *args, **kwargs)
        component.pack(fill=tk.BOTH, expand=True)
        self._subwindows[win_id] = (toplevel, component)

    def close_subwindow(self, win_id: str) -> None:
        """特定のサブウィンドウを閉じる"""
        if win_id not in self._subwindows:
            return
        toplevel, component = self._subwindows.pop(win_id)
        try:
            component.destroy()
        except Exception:
            pass
        toplevel.destroy()

    def close_all_subwindows(self) -> None:
        """全サブウィンドウをまとめて閉じる"""
        for wid in list(self._subwindows):
            self.close_subwindow(wid)

    def run(
        self,
        use_async: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        poll_interval: int = 50,
    ) -> None:
        """
        メインループ開始。
        :param use_async: True のとき asyncio イベントループも併用
        :param loop: 使用する asyncio イベントループ (None で既定ループ)
        :param poll_interval: asyncio ポーリング間隔 (ms)
        """
        # ウィンドウクローズ時の処理をバインド
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        if not use_async:
            # tkinter だけ回す
            self.mainloop()
        else:
            loop = loop or asyncio.get_event_loop()
            # 定期ポーリング開始
            self.after(poll_interval, _default_poll, loop, self, poll_interval)
            self.mainloop()
            # 終了後、asyncio の後片付け
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass

    def on_closing(self) -> None:
        """終了時のクリーンアップ"""
        self.close_all_subwindows()
        self.destroy()


def build_application_class(root_cls: Type[R]) -> Type[R]:
    """
    root_cls（tk.Tk 派生）と ApplicationMixin を合成した
    アプリケーションクラスを動的生成して返す
    """
    return type(f"ApplicationWith{root_cls.__name__}", (root_cls, ApplicationMixin), {})


# 使い方例:
# from ttkthemes import ThemedTk
# AppClass = build_application_class(ThemedTk)
# app = AppClass(title="MyApp", geometry="1024x768")
# # 通常モード
# app.run()
# # asyncio 併用モード
# app.run(use_async=True, poll_interval=100)
