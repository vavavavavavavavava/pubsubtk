import tkinter as tk
from abc import ABC, abstractmethod
from typing import Any


class UIMixin(ABC):
    """
    UIコンポーネント用の基底Mixin。

    - __init__でsetup_ui()を自動呼び出し
    - サブクラスはsetup_ui()のみを実装すればよい
    - レイアウトやウィジェット構築の共通化
    """

    def __init__(self, parent: tk.Widget, **kwargs: Any):
        # 継承先の tk.Frame / ttk.Frame.__init__ を呼び出す
        super().__init__(parent, **kwargs)
        self.setup_ui()

    @abstractmethod
    def setup_ui(self) -> None:
        """
        ウィジェット構築とレイアウトを行うメソッド。
        サブクラスで実装する。
        """
        pass
