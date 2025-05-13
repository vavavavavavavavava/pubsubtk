import tkinter as tk
from abc import abstractmethod
from tkinter import ttk
from typing import Any

from pubsubtk.core.api import get_store
from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.ui.base.component_base import UIMixin


class ContainerMixin(UIMixin, PubSubBase):
    """
    PubSub 連携用コンテナコンポーネント Mixin
    """

    def __init__(self, parent: tk.Widget, **kwargs: Any):
        super().__init__(parent, **kwargs)
        PubSubBase.__init__(self)
        self.store = get_store()
        self.setup_subscriptions()
        self.refresh_from_state()

    @abstractmethod
    def setup_subscriptions(self) -> None:
        """Store の更新購読を設定するメソッド"""
        ...

    @abstractmethod
    def refresh_from_state(self) -> None:
        """購読通知または初期化時に UI を更新するメソッド"""
        ...

    def destroy(self) -> None:
        self.teardown()
        super().destroy()


# tk.Frame ベース の抽象クラス
class ContainerComponentTk(tk.Frame, ContainerMixin):
    """純粋な tk.Frame ベース の PubSub 連携コンテナ"""

    pass


# ttk.Frame ベース の抽象クラス
class ContainerComponentTtk(ttk.Frame, ContainerMixin):
    """テーマ対応 ttk.Frame ベース の PubSub 連携コンテナ"""

    pass
