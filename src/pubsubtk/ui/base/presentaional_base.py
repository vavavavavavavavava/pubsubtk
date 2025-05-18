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
        tk.Frame.__init__(self, master=parent, *args, **kwargs)
        PresentationalMixin.__init__(self, *args, **kwargs)


# ttk.Frame ベース の抽象クラス
class PresentationalComponentTtk(PresentationalMixin, ttk.Frame):
    """
    テーマ対応ttk.Frameベースの表示専用コンポーネント。
    """

    def __init__(self, parent: tk.Widget, *args, **kwargs):
        tk.Frame.__init__(self, master=parent, *args, **kwargs)
        PresentationalMixin.__init__(self, *args, **kwargs)
