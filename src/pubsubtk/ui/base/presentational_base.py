"""
src/pubsubtk/ui/base/presentational_base.py

イベント発火機能を備えた表示専用 UI コンポーネント用基底クラス。
"""

import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from typing import Any, Callable, Dict


class PresentationalMixin(ABC):
    """
    表示専用コンポーネント用のMixin。

    - 任意のイベントハンドラ登録・発火機能を持つ
    """

    def __init__(self, *args, **kwargs):
        """Mixin の初期化処理。

        Notes:
            渡された ``*args`` と ``**kwargs`` は ``self.args`` / ``self.kwargs``
            として保持されます。サブウィンドウで使用する場合は ``open_subwindow``
            が ``win_id`` を自動付与するため、 ``self.kwargs["win_id"]`` を利用して
            自身を閉じられます。今後同様のデフォルト引数が追加される可能性があります。
        """

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
        """tk.Frame ベースの表示コンポーネントを初期化する。"""

        tk.Frame.__init__(self, master=parent)
        PresentationalMixin.__init__(self, *args, **kwargs)


# ttk.Frame ベース の抽象クラス
class PresentationalComponentTtk(PresentationalMixin, ttk.Frame):
    """
    テーマ対応ttk.Frameベースの表示専用コンポーネント。
    """

    def __init__(self, parent: tk.Widget, *args, **kwargs):
        """ttk.Frame ベースの表示コンポーネントを初期化する。"""

        ttk.Frame.__init__(self, master=parent)
        PresentationalMixin.__init__(self, *args, **kwargs)
