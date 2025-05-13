import tkinter as tk
from abc import ABC, abstractmethod
from typing import Any


class UIMixin(ABC):
    """
    ・__init__ で setup_ui() を呼び出す
    ・サブクラスは setup_ui() を実装するだけ
    """

    def __init__(self, parent: tk.Widget, **kwargs: Any):
        # 継承先の tk.Frame / ttk.Frame.__init__ を呼び出す
        super().__init__(parent, **kwargs)
        self.setup_ui()

    @abstractmethod
    def setup_ui(self) -> None:
        """
        ウィジェット構築とレイアウトを行うメソッド
        """
        pass
