import asyncio
import tkinter as tk
from typing import Any, Dict, Optional, Tuple, Type

from ttkthemes import ThemedTk

from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.topic.topics import DefaultNavigateTopic


def _default_poll(loop: asyncio.AbstractEventLoop, root: tk.Tk, interval: int) -> None:
    try:
        loop.call_soon(loop.stop)
        loop.run_forever()
    except Exception:
        pass
    root.after(interval, _default_poll, loop, root, interval)


class ApplicationCommon(PubSubBase):
    """Tk/Ttk いずれのウィンドウクラスでも共通の機能を提供する Mixin"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            DefaultNavigateTopic.CLOSE_ALL_SUBWINDOWS,
            self.close_all_subwindows,
        )

    def switch_container(
        self,
        cls: Type[tk.Widget],
        *args: Any,
        **kwargs: Any,
    ) -> None:
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
        if win_id in self._subwindows:
            self._subwindows[win_id][0].lift()
            return
        toplevel = tk.Toplevel(self)
        comp = cls(toplevel, *args, **kwargs)
        comp.pack(fill=tk.BOTH, expand=True)
        self._subwindows[win_id] = (toplevel, comp)

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
        self, title: str = "Tk App", geometry: str = "800x600", *args, **kwargs
    ):
        # **first** initialize the actual Tk
        tk.Tk.__init__(self, *args, **kwargs)
        # **then** initialize the PubSub mixin
        ApplicationCommon.__init__(self)
        # now do your common window setup
        self.init_common(title, geometry)


class ThemedApplication(ApplicationCommon, ThemedTk):
    def __init__(
        self,
        theme: str = "arc",
        title: str = "Themed App",
        geometry: str = "800x600",
        *args,
        **kwargs,
    ):
        # initialize the themed‐Tk
        ThemedTk.__init__(self, *args, theme=theme, **kwargs)
        # mixin init
        ApplicationCommon.__init__(self)
        # then common setup
        self.init_common(title, geometry)
