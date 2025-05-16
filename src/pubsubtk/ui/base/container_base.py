import tkinter as tk
from abc import abstractmethod
from tkinter import ttk
from typing import Any

from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.store.store import get_store
from pubsubtk.ui.base.component_base import UIMixin


class ContainerMixin(UIMixin, PubSubBase):
    """
    PubSub連携用のコンテナコンポーネントMixin。

    - Storeインスタンスを取得し、購読設定・状態反映を自動実行
    - setup_subscriptions()/refresh_from_state()をサブクラスで実装
    - destroy時に購読解除(teardown)も自動
    """

    def __init__(self, parent: tk.Widget, **kwargs: Any):
        super().__init__(parent, **kwargs)
        PubSubBase.__init__(self)
        self.store = get_store()
        self.setup_subscriptions()
        self.refresh_from_state()

    @abstractmethod
    def setup_subscriptions(self) -> None:
        """
        Storeの更新購読を設定するメソッド。
        サブクラスで実装する。
        """
        ...

    @abstractmethod
    def refresh_from_state(self) -> None:
        """
        購読通知または初期化時にUIを状態で更新するメソッド。
        サブクラスで実装する。
        """
        ...

    def destroy(self) -> None:
        self.teardown()
        super().destroy()


# tk.Frame ベース の抽象クラス
class ContainerComponentTk(tk.Frame, ContainerMixin):
    """
    標準tk.FrameベースのPubSub連携コンテナ。
    """

    pass


# ttk.Frame ベース の抽象クラス
class ContainerComponentTtk(ttk.Frame, ContainerMixin):
    """
    テーマ対応ttk.FrameベースのPubSub連携コンテナ。
    """

    pass
