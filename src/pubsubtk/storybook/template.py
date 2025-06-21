# storybook/template.py - StorybookTemplate
"""2 スロット (sidebar / preview) を持つテンプレート。"""

from tkinter import ttk

from pubsubtk import TemplateComponentTtk
from pubsubtk.storybook.state import StorybookState


class StorybookTemplate(TemplateComponentTtk[StorybookState]):
    """Storybook の基本レイアウト（テーマ対応）"""

    def define_slots(self):
        # メインレイアウト設定
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # サイドバー（左側）
        sidebar_frame = ttk.Frame(self, width=250)
        sidebar_frame.grid(
            row=0, column=0, sticky="nsew", padx=(2, 1), pady=2
        )
        sidebar_frame.grid_propagate(False)  # 幅を固定

        # プレビューエリア（中央）
        preview_frame = ttk.LabelFrame(self, text="Preview", padding=5)
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(1, 2), pady=2)

        return {
            "sidebar": sidebar_frame,
            "preview": preview_frame,
        }
