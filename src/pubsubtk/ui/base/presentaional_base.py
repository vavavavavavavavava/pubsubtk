import tkinter as tk
from abc import abstractmethod
from tkinter import ttk
from typing import Any, Callable, Dict

from pubsubtk.ui.base.component_base import UIMixin


class PresentationalMixin(UIMixin):
    """
    表示専用コンポーネント用のMixin。

    - 外部データでUIを更新するupdate_data()を抽象メソッドとして提供
    - 任意のイベントハンドラ登録・発火機能を持つ
    """

    def __init__(self, parent: tk.Widget, **kwargs: Any):
        self._handlers: Dict[str, Callable[..., Any]] = {}
        super().__init__(parent, **kwargs)

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
class PresentationalComponentTk(tk.Frame, PresentationalMixin):
    """
    標準tk.Frameベースの表示専用コンポーネント。
    """

    pass


# ttk.Frame ベース の抽象クラス
class PresentationalComponentTtk(ttk.Frame, PresentationalMixin):
    """
    テーマ対応ttk.Frameベースの表示専用コンポーネント。
    """

    pass
