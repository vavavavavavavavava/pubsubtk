from __future__ import annotations

import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, Generic, TypeVar

from pydantic import BaseModel

from pubsubtk.store.store import Store
from pubsubtk.ui.base.container_base import ContainerMixin

if TYPE_CHECKING:
    from pubsubtk.ui.types import ComponentType

TState = TypeVar("TState", bound=BaseModel)


class TemplateMixin(ABC, Generic[TState]):
    """
    テンプレートコンポーネント用のMixin。

    複数のスロット（区画）を定義し、各スロットに独立してコンポーネントを配置できる。
    ヘッダー・フッターなど固定部分と可変部分を分離したレイアウトを実現。

    Note:
        テンプレート自体は状態を持たず、レイアウト定義とスロット管理のみを行う。
        各スロットに配置されるコンポーネントが独自に状態管理を行う。
    """

    def __init__(self, store: Store[TState], *args, **kwargs):
        self.store = store
        self._slots: Dict[str, tk.Widget] = {}
        self._slot_contents: Dict[str, tk.Widget] = {}

        # テンプレートのセットアップ
        self.setup_template()
        self._slots = self.define_slots()

    def setup_template(self) -> None:
        """
        テンプレート固有の初期化処理（必要に応じてオーバーライド）。
        define_slots()の前に呼ばれる。
        """
        pass

    @abstractmethod
    def define_slots(self) -> Dict[str, tk.Widget]:
        """
        スロット（区画）を定義する。

        Returns:
            Dict[str, tk.Widget]: {"スロット名": フレームWidget} の辞書

        Example:
            # ヘッダー
            self.header_frame = tk.Frame(self, height=60, bg='navy')
            self.header_frame.pack(fill=tk.X)

            # メインコンテンツ
            self.main_frame = tk.Frame(self)
            self.main_frame.pack(fill=tk.BOTH, expand=True)

            # フッター
            self.footer_frame = tk.Frame(self, height=30, bg='gray')
            self.footer_frame.pack(fill=tk.X)

            return {
                "header": self.header_frame,
                "main": self.main_frame,
                "footer": self.footer_frame
            }
        """
        pass

    def switch_slot_content(
        self, slot_name: str, cls: ComponentType, kwargs: dict = None
    ) -> None:
        """
        指定スロットのコンテンツを切り替える。

        Args:
            slot_name: スロット名
            cls: コンポーネントクラス（Container/Presentational両対応）
            kwargs: コンポーネントに渡す引数
        """
        if slot_name not in self._slots:
            raise ValueError(f"Unknown slot: {slot_name}")

        # 既存のコンテンツを破棄
        if slot_name in self._slot_contents:
            self._slot_contents[slot_name].destroy()

        # 新しいコンテンツを作成
        parent_frame = self._slots[slot_name]
        content = self._create_component_for_slot(cls, parent_frame, kwargs)
        content.pack(fill=tk.BOTH, expand=True)

        self._slot_contents[slot_name] = content

    def _create_component_for_slot(
        self, cls: ComponentType, parent: tk.Widget, kwargs: dict = None
    ) -> tk.Widget:
        """スロット用のコンポーネント生成"""
        kwargs = kwargs or {}

        # ContainerMixinを継承しているかチェック
        is_container = issubclass(cls, ContainerMixin)

        if is_container:
            return cls(parent=parent, store=self.store, **kwargs)
        else:
            return cls(parent=parent, **kwargs)

    def get_slots(self) -> Dict[str, tk.Widget]:
        """定義されているスロットの辞書を返す"""
        return self._slots.copy()

    def get_slot_content(self, slot_name: str) -> tk.Widget | None:
        """指定スロットの現在のコンテンツを返す"""
        return self._slot_contents.get(slot_name)

    def has_slot(self, slot_name: str) -> bool:
        """指定した名前のスロットが存在するかチェック"""
        return slot_name in self._slots

    def clear_slot(self, slot_name: str) -> None:
        """指定スロットのコンテンツをクリアする"""
        if slot_name in self._slot_contents:
            self._slot_contents[slot_name].destroy()
            del self._slot_contents[slot_name]

    def clear_all_slots(self) -> None:
        """すべてのスロットのコンテンツをクリアする"""
        for slot_name in list(self._slot_contents.keys()):
            self.clear_slot(slot_name)


class TemplateComponentTk(TemplateMixin[TState], tk.Frame, Generic[TState]):
    """
    標準tk.Frameベースのテンプレートコンポーネント。
    """

    def __init__(self, parent: tk.Widget, store: Store[TState], *args, **kwargs):
        tk.Frame.__init__(self, master=parent)
        TemplateMixin.__init__(self, store=store, *args, **kwargs)


class TemplateComponentTtk(TemplateMixin[TState], ttk.Frame, Generic[TState]):
    """
    テーマ対応ttk.Frameベースのテンプレートコンポーネント。
    """

    def __init__(self, parent: tk.Widget, store: Store[TState], *args, **kwargs):
        ttk.Frame.__init__(self, master=parent)
        TemplateMixin.__init__(self, store=store, *args, **kwargs)
