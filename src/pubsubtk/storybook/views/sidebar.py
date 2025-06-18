# storybook/views/sidebar.py - SidebarView
"""Story ツリーを表示するサイドバー。"""

import tkinter as tk
from tkinter import ttk

from pubsubtk import ContainerComponentTk

from ..registry import StoryRegistry
from ..state import StorybookState
from ..topic import SBTopic


class SidebarView(ContainerComponentTk[StorybookState]):
    """左側のツリーサイドバー"""

    def setup_ui(self):
        self.tree = ttk.Treeview(self, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self._populate()
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def setup_subscriptions(self):
        # 必要に応じて状態変更を購読
        pass

    def refresh_from_state(self):
        # 状態変更時の再描画（必要に応じて実装）
        pass

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
        if sel:
            self.publish(SBTopic.SELECT_STORY, story_id=sel[0])
