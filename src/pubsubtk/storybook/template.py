# storybook/template.py - StorybookTemplate
"""3 スロット (sidebar / preview / knobs) を持つテンプレート。"""

import tkinter as tk

from pubsubtk import TemplateComponentTk

from .state import StorybookState


class StorybookTemplate(TemplateComponentTk[StorybookState]):
    """Storybook の基本レイアウト"""

    def define_slots(self):
        # レイアウト
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = tk.Frame(self, width=220, borderwidth=1, relief=tk.SUNKEN)
        sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)
        preview = tk.Frame(self, borderwidth=1, relief=tk.SUNKEN)
        preview.grid(row=0, column=1, sticky="nsew")
        knobs = tk.Frame(self, borderwidth=1, relief=tk.SUNKEN, height=180)
        knobs.grid(row=1, column=1, sticky="nsew")

        return {"sidebar": sidebar, "preview": preview, "knobs": knobs}
