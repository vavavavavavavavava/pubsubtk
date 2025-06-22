# storybook/template.py - StorybookTemplate
"""3 スロット (sidebar / preview / knobs) を持つテンプレート。"""

from tkinter import ttk

from pubsubtk import TemplateComponentTtk

from ..core.state import StorybookState


class StorybookTemplate(TemplateComponentTtk[StorybookState]):
    """Storybook の基本レイアウト（テーマ対応）"""

    def define_slots(self):
        # メインレイアウト設定
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # サイドバー（左側）
        sidebar_frame = ttk.Frame(self, width=250)
        sidebar_frame.grid(
            row=0, column=0, sticky="nsew", padx=(2, 1), pady=2, rowspan=2
        )
        sidebar_frame.grid_propagate(False)  # 幅を固定

        # プレビューエリア（中央上）
        preview_frame = ttk.LabelFrame(self, text="Preview", padding=5)
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(1, 2), pady=(2, 1))

        # Knobパネル（中央下）
        knobs_frame = ttk.LabelFrame(self, text="Controls", padding=5)
        knobs_frame.grid(row=1, column=1, sticky="nsew", padx=(1, 2), pady=(1, 2))

        # 高さ比率設定（Preview 70%, Knobs 30%）
        self.grid_rowconfigure(0, weight=7)  # Previewエリア
        self.grid_rowconfigure(1, weight=3)  # Knobエリア

        return {
            "sidebar": sidebar_frame,
            "preview": preview_frame,
            "knobs": knobs_frame,
        }
