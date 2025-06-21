# storybook/views/sidebar.py - SidebarView
"""Story ツリーを表示するサイドバー。"""

import tkinter as tk
from tkinter import ttk

from pubsubtk import ContainerComponentTtk

from ..core.registry import StoryRegistry
from ..core.state import StorybookState
from ..processors.topics import SBTopic


class SidebarView(ContainerComponentTtk[StorybookState]):
    """左側のツリーサイドバー（テーマ対応）"""

    def setup_ui(self):
        # ヘッダー
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        title_label = ttk.Label(header_frame, text="Stories", font=("", 12, "bold"))
        title_label.pack(side=tk.LEFT)

        # 区切り線
        separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, padx=5, pady=5)

        # ツリービュー用フレーム
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # ツリービュー
        self.tree = ttk.Treeview(tree_frame, show="tree")

        # スクロールバー
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # レイアウト
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # データ投入とイベント設定
        self._populate()
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # ツリーのスタイル調整
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)

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
                    self.tree.insert(
                        parent_id, "end", iid=node_id, text=f"📁 {seg}", open=True
                    )
                parent_id = node_id
            self.tree.insert(
                parent_id,
                "end",
                iid=meta.id,
                text=f"📄 {meta.title}",
                values=(meta.id,),
            )

    def _on_select(self, _):
        sel = self.tree.selection()
        if sel:
            self.publish(SBTopic.SELECT_STORY, story_id=sel[0])
