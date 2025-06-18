# storybook/views/sidebar.py - SidebarView
"""Story ツリーを表示するサイドバー。"""

import tkinter as tk
from tkinter import ttk

from pubsubtk import PresentationalComponentTk

from ..registry import StoryRegistry
from ..topic import SBTopic


class SidebarView(PresentationalComponentTk):
    """左側のツリーサイドバー"""

    def setup_ui(self):
        self.tree = ttk.Treeview(self, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self._populate()
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _populate(self):
        for meta in StoryRegistry.list():
            parent_id = ""
            for seg in meta.path:
                node_id = f"{parent_id}.{seg}" if parent_id else seg
                if not self.tree.exists(node_id):
                    self.tree.insert(parent_id, "end", iid=node_id, text=seg, open=True)
                parent_id = node_id
            self.tree.insert(
                parent_id, "end", iid=meta.id, text=meta.title, values=(meta.id,)
            )

    def _on_select(self, _):
        sel = self.tree.selection()
        if sel and hasattr(self, "_publish_callback") and self._publish_callback:
            self._publish_callback(SBTopic.SELECT_STORY, {"story_id": sel[0]})

    def set_publish_callback(self, callback):
        """外部からPubSub発行用コールバックを設定"""
        self._publish_callback = callback
